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
        # If there is no diff for any of these items, the user reverted back
        # to the original state. In this case, do not make a commit, as it
        # would be an empty commit.
        if not self._git.index.diff(other=None, paths=self._files_added + self._files_removed):
            return

        # Update the index with the added/removed files.
        for filename in self._files_added:
            self._git.index.add(filename)
        for filename in self._files_removed:
            self._git.index.remove(filename)
        self._files_added.clear()

        git_author = git.Actor(*user.get_git_author())

        self._git.index.commit(
            commit_message,
            author=git_author,
            committer=self._git_commiter,
        )

    def file_write(self, filename: str, content, mode="w") -> None:
        super().file_write(filename, content, mode)
        self._files_added.append(filename)

    def file_remove(self, filename: str) -> None:
        super().file_remove(filename)
        self._files_removed.append(filename)

    def file_rename(self, old_filename: str, new_filename: str) -> None:
        super().file_rename(old_filename, new_filename)
        self._files_removed.append(old_filename)
        self._files_added.append(new_filename)


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
