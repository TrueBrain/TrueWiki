import asyncio
import click
import git
import logging
import multiprocessing
import sys

from concurrent import futures
from openttd_helpers import click_helper

from . import local

log = logging.getLogger(__name__)

GIT_USERNAME = None
GIT_EMAIL = None

GIT_BUSY = asyncio.Event()
GIT_BUSY.set()


class OutOfProcessStorage:
    def __init__(self, git_commiter, folder, ssh_command):
        self._git_commiter = git_commiter
        self._folder = folder
        self._ssh_command = ssh_command
        self._git = git.Repo(self._folder)

    def commit(self, git_author, commit_message, files_added, files_changed, files_removed):
        # We run this in a separate process, because GitPython is blocking.
        # And something like "git push" can take 4+ seconds. This would be
        # annoying for the end-user. But by delegating it to its own process,
        # we have to take care of some race-conditions. For example, it can
        # happen that a user makes an unrelated change, then makes a page and
        # removes it directly after. As the unrelated change is taking 4+
        # seconds, the next commit tries to add a page that is already removed.
        # In that case, we simply ignore the change, as there is nothing else
        # we can do.
        # It has to be noted, it is rather unlike that a human makes this
        # happen, but it is happening a lot with our end-to-end tests.

        if not files_added and not files_removed:
            # If there is no diff for any of these items, the user reverted back
            # to the original state. In this case, do not make a commit, as it
            # would be an empty commit.
            if not self._git.index.diff(other=None, paths=files_changed):
                return True

        # Update the index with the added/removed files.
        for filename in files_added + files_changed:
            try:
                self._git.index.add(filename)
            except FileNotFoundError:
                # Sadly, a newer change has removed the file. So this
                # change will be lost in history.
                pass
        for filename in files_removed:
            try:
                self._git.index.remove(filename)
            except git.exc.GitCommandError:
                # The file was already removed or never existed.
                pass

        git_author = git.Actor(*git_author)

        self._git.index.commit(
            commit_message,
            author=git_author,
            committer=git.Actor(*self._git_commiter),
        )

        return True


def check_for_exception(task):
    exception = task.exception()
    if exception and not isinstance(exception, asyncio.exceptions.CancelledError):
        log.exception("Exception in git command", exc_info=exception)

        # We terminate the application, as this is a real problem from which we
        # cannot recover cleanly. This is needed, as we run in a co-routine, and
        # there is no other way to notify the main thread we are terminating.
        sys.exit(1)


class Storage(local.Storage):
    out_of_process_class = OutOfProcessStorage

    def __init__(self, ssh_command=None):
        super().__init__()

        self._ssh_command = ssh_command

        self._files_added = []
        self._files_changed = []
        self._files_removed = []

    def prepare(self):
        super().prepare()

        try:
            self._git = git.Repo(self.folder)
        except git.exc.NoSuchPathError:
            self._git = self._init_repository()
        except git.exc.InvalidGitRepositoryError:
            self._git = self._init_repository()
        return self._git

    def _init_repository(self):
        _git = git.Repo.init(self.folder)
        # Always make sure there is a commit in the working tree, otherwise
        # HEAD is invalid, which results in other nasty problems.
        _git.index.commit(
            "Add: initial empty commit",
            author=git.Actor(GIT_USERNAME, GIT_EMAIL),
            committer=git.Actor(GIT_USERNAME, GIT_EMAIL),
        )

        # Import any file in the data directory.
        if _git.untracked_files:
            for filename in _git.untracked_files:
                _git.index.add(filename)
            _git.index.commit(
                "Add: initial files",
                author=git.Actor(GIT_USERNAME, GIT_EMAIL),
                committer=git.Actor(GIT_USERNAME, GIT_EMAIL),
            )

        return _git

    async def _run_out_of_process_async(self, folder, ssh_command, callback, func, *args):
        await GIT_BUSY.wait()
        GIT_BUSY.clear()

        try:
            out_of_process = self.out_of_process_class((GIT_USERNAME, GIT_EMAIL), folder, ssh_command)

            # Run the reload in a new process, so we don't block the rest of the
            # server while doing this job.
            loop = asyncio.get_event_loop()
            # Use "spawn" over "fork", as we don't need any variable from our
            # current process. This heavily cuts back on memory usage, but it
            # takes a bit longer to start up.
            mp_context = multiprocessing.get_context("spawn")
            with futures.ProcessPoolExecutor(max_workers=1, mp_context=mp_context) as executor:
                task = loop.run_in_executor(executor, getattr(out_of_process, func), *args)
                result = await task
        finally:
            GIT_BUSY.set()

        # Task indicated something went wrong; initiate a full reload.
        if result is False:
            self.reload()
            return

        if callback:
            callback()

    def _run_out_of_process(self, callback, func, *args):
        loop = asyncio.get_event_loop()
        task = loop.create_task(self._run_out_of_process_async(self._folder, self._ssh_command, callback, func, *args))
        task.add_done_callback(check_for_exception)

    def commit(self, user, commit_message):
        args = (
            user.get_git_author(),
            commit_message,
            self._files_added[:],
            self._files_changed[:],
            self._files_removed[:],
        )
        self._files_added.clear()
        self._files_changed.clear()
        self._files_removed.clear()

        self._run_out_of_process(self.commit_done, "commit", *args)

    def commit_done(self):
        pass

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

    def get_file_nonce(self, filename: str) -> str:
        return self._git.head.commit.hexsha


@click_helper.extend
@click.option(
    "--storage-git-username", help="Username to use when creating commits.", default="Librarian", show_default=True
)
@click.option(
    "--storage-git-email",
    help="Email to use when creating commits.",
    default="wiki@localhost",
    show_default=True,
)
def click_storage_git(storage_git_username, storage_git_email):
    global GIT_USERNAME, GIT_EMAIL

    GIT_USERNAME = storage_git_username
    GIT_EMAIL = storage_git_email
