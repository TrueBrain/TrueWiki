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


class OutOfProcessStorage(GitOutOfProcessStorage):
    def _remove_empty_folders(self, parent_folder):
        removed = False
        for root, folders, files in os.walk(parent_folder, topdown=False):
            if root.startswith(".git"):
                continue

            if not folders and not files:
                os.rmdir(root)
                removed = True

        return removed

    def fetch_latest(self):
        log.info("Updating storage to latest version from GitHub")

        origin = self._git.remotes.origin

        # Checkout the latest master, removing and commits/file changes local
        # might have.
        with self._git.git.custom_environment(GIT_SSH_COMMAND=self._ssh_command):
            try:
                origin.fetch()
            except git.exc.BadName:
                # When the garbage collector kicks in, GitPython gets confused and
                # throws a BadName. The best solution? Just run it again.
                origin.fetch()

        origin.refs.master.checkout(force=True, B="master")
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
            log.error("No GitHub private key supplied; cannot push to GitHub.")
            return True

        try:
            with self._git.git.custom_environment(GIT_SSH_COMMAND=self._ssh_command):
                self._git.remotes.origin.push()
        except Exception:
            log.exception("Git push failed; reloading from GitHub")
            return False

        return True


class Storage(GitStorage):
    out_of_process_class = OutOfProcessStorage

    def __init__(self):
        super().__init__()

        # We need to write the private key to disk: GitPython can only use
        # SSH-keys that are written on disk.
        if _github_private_key:
            self._github_private_key_file = tempfile.NamedTemporaryFile()
            self._github_private_key_file.write(_github_private_key)
            self._github_private_key_file.flush()

            self._ssh_command = f"ssh -i {self._github_private_key_file.name}"

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
        self._run_out_of_process(self._reload_done, "fetch_latest")

    def _reload_done(self):
        super().reload()

    def commit_done(self):
        self._run_out_of_process(None, "push")

    def get_history_url(self, page):
        page = urllib.parse.quote(page)
        return f"{_github_history_url}/commits/master/{page}"

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
    help="Base64-encoded private key to access GitHub." "Always use this via an environment variable!",
)
def click_storage_github(storage_github_url, storage_github_history_url, storage_github_private_key):
    global _github_url, _github_history_url, _github_private_key

    if storage_github_history_url is None:
        storage_github_history_url = storage_github_url

    _github_url = storage_github_url
    _github_history_url = storage_github_history_url
    if storage_github_private_key:
        _github_private_key = base64.b64decode(storage_github_private_key)
