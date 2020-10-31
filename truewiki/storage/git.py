import click
import git

from openttd_helpers import click_helper

from . import local

GIT_USERNAME = None
GIT_EMAIL = None


class Storage(local.Storage):
    def __init__(self):
        super().__init__()

        self._git_author = git.Actor(GIT_USERNAME, GIT_EMAIL)

    def prepare(self):
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
            author=self._git_author,
            committer=self._git_author,
        )

    def commit(self, files, commit_message):
        for filename in files:
            self._git.index.add(filename)

        commit_message = f"Update: {commit_message}"

        self._git.index.commit(
            commit_message,
            author=self._git_author,
            committer=self._git_author,
        )


@click_helper.extend
@click.option(
    "--index-local-username", help="Username to use when creating commits.", default="Librarian", show_default=True
)
@click.option(
    "--index-local-email",
    help="Email to use when creating commits.",
    default="content-api@openttd.org",
    show_default=True,
)
def click_index_local(index_local_username, index_local_email):
    global GIT_USERNAME, GIT_EMAIL

    GIT_USERNAME = index_local_username
    GIT_EMAIL = index_local_email
