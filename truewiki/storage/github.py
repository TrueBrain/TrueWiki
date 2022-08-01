import base64
import click
import git
import logging
import tempfile
import os
import urllib

from openttd_helpers import click_helper

from .git import (
    OutOfProcessStorage as GitOutOfProcessStorage,
    Storage as GitStorage,
)

log = logging.getLogger(__name__)

_github_private_key = None
_github_url = None
_github_history_url = None
_github_branch = None


class OutOfProcessStorage(GitOutOfProcessStorage):
    name = "GitHub"

    def _remove_empty_folders(self, parent_folder):
        removed = False
        for root, folders, files in os.walk(parent_folder, topdown=False):
            if root.startswith(".git"):
                continue

            if not folders and not files:
                os.rmdir(root)
                removed = True

        return removed

    def fetch_latest(self, branch):
        log.info(f"Updating storage to latest version from {self.name}")

        origin = self._git.remotes.origin

        # Checkout the latest default branch, removing and commits/file
        # changes local might have.
        with self._git.git.custom_environment(GIT_SSH_COMMAND=self._ssh_command):
            try:
                origin.fetch()
            except git.exc.BadName:
                # When the garbage collector kicks in, GitPython gets confused and
                # throws a BadName. The best solution? Just run it again.
                origin.fetch()

        origin.refs[branch].checkout(force=True, B=branch)
        for file_name in self._git.untracked_files:
            os.unlink(f"{self._folder}/{file_name}")

        # We might end up with empty folders, which the rest of the
        # application doesn't really like. So remove them. Keep repeating the
        # function until no folders are removed anymore.
        while self._remove_empty_folders(self._folder):
            pass

        return True

    def push(self):
        if not self._ssh_command:
            log.error(f"No {self.name} private key supplied; cannot push to {self.name}.")
            return True

        try:
            with self._git.git.custom_environment(GIT_SSH_COMMAND=self._ssh_command):
                self._git.remotes.origin.push()
        except Exception:
            log.exception(f"Git push failed; reloading from {self.name}")
            return False

        return True


class Storage(GitStorage):
    out_of_process_class = OutOfProcessStorage

    def __init__(self):
        # We need to write the private key to disk: GitPython can only use
        # SSH-keys that are written on disk.
        if _github_private_key:
            self._github_private_key_file = tempfile.NamedTemporaryFile()
            self._github_private_key_file.write(_github_private_key)
            self._github_private_key_file.flush()

            super().__init__(f"ssh -i {self._github_private_key_file.name}")
        else:
            super().__init__()

    def prepare(self):
        _git = super().prepare()

        # Make sure the origin is set correctly
        if "origin" not in _git.remotes:
            _git.create_remote("origin", _github_url)
        origin = _git.remotes.origin
        if origin.url != _github_url:
            origin.set_url(_github_url)

        return _git

    def reload(self):
        self._run_out_of_process(self._reload_done, "fetch_latest", _github_branch)

    def _reload_done(self):
        super().reload()

    def commit_done(self):
        super().commit_done()
        self._run_out_of_process(None, "push")

    def get_history_url(self, page):
        page = urllib.parse.quote(page)
        return f"{_github_history_url}/commits/{_github_branch}/{page}"

    def get_repository_url(self):
        return _github_history_url


@click_helper.extend
@click.option(
    "--storage-github-url",
    help="Repository URL on GitHub.",
    default="https://github.com/TrueBrain/wiki-example",
    show_default=True,
    metavar="URL",
)
@click.option(
    "--storage-github-history-url",
    help="Repository URL on GitHub to visit history (defaults to --storage-github-url).",
    default=None,
    show_default=True,
    metavar="URL",
)
@click.option(
    "--storage-github-private-key",
    help="Base64-encoded private key to access GitHub. Always use this via an environment variable!",
)
@click.option(
    "--storage-github-branch",
    help="Branch of the GitHub repository to use.",
    default="main",
    show_default=True,
    metavar="branch",
)
def click_storage_github(
    storage_github_url,
    storage_github_history_url,
    storage_github_private_key,
    storage_github_branch,
):
    global _github_url, _github_history_url, _github_private_key, _github_branch

    if storage_github_history_url is None:
        storage_github_history_url = storage_github_url

    _github_url = storage_github_url
    _github_history_url = storage_github_history_url
    _github_branch = storage_github_branch
    if storage_github_private_key:
        _github_private_key = base64.b64decode(storage_github_private_key)
