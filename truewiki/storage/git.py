import click
import git

from openttd_helpers import click_helper

from . import local

GIT_USERNAME = None
GIT_EMAIL = None


class Storage(local.Storage):
    def __init__(self):
        super().__init__()

        self._git_commiter = git.Actor(GIT_USERNAME, GIT_EMAIL)
        self._files_added = []
        self._files_changed = []
        self._files_removed = []

    def prepare(self):
        super().prepare()

        try:
            self._git = git.Repo(self.folder)
        except git.exc.NoSuchPathError:
            self._init_repository()
        except git.exc.InvalidGitRepositoryError:
            self._init_repository()

    def _init_repository(self):
        self._git = git.Repo.init(self.folder)
        # Always make sure there is a commit in the working tree, otherwise
        # HEAD is invalid, which results in other nasty problems.
        self._git.index.commit(
            "Add: initial empty commit",
            author=self._git_commiter,
            committer=self._git_commiter,
        )

    def commit(self, user, commit_message):
        if not self._files_added and not self._files_removed:
            # If there is no diff for any of these items, the user reverted back
            # to the original state. In this case, do not make a commit, as it
            # would be an empty commit.
            if not self._git.index.diff(other=None, paths=self._files_changed):
                return

        # Update the index with the added/removed files.
        for filename in self._files_added + self._files_changed:
            self._git.index.add(filename)
        for filename in self._files_removed:
            self._git.index.remove(filename)
        self._files_added.clear()
        self._files_changed.clear()
        self._files_removed.clear()

        git_author = git.Actor(*user.get_git_author())

        self._git.index.commit(
            commit_message,
            author=git_author,
            committer=self._git_commiter,
        )

    def file_write(self, filename: str, content, mode="w") -> None:
        if self.file_exists(filename):
            self._files_changed.append(filename)
        else:
            self._files_added.append(filename)

        super().file_write(filename, content, mode)

    def file_remove(self, filename: str) -> None:
        self._files_removed.append(filename)

        super().file_remove(filename)

    def file_rename(self, old_filename: str, new_filename: str) -> None:
        self._files_removed.append(old_filename)
        self._files_added.append(new_filename)

        super().file_rename(old_filename, new_filename)


@click_helper.extend
@click.option(
    "--storage-git-username", help="Username to use when creating commits.", default="Librarian", show_default=True
)
@click.option(
    "--storage-git-email",
    help="Email to use when creating commits.",
    default="wiki@openttd.org",
    show_default=True,
)
def click_storage_git(storage_git_username, storage_git_email):
    global GIT_USERNAME, GIT_EMAIL

    GIT_USERNAME = storage_git_username
    GIT_EMAIL = storage_git_email
