import asyncio
import base64
import click
import git
import logging
import tempfile
import os
import urllib

from openttd_helpers import click_helper

from .git import Storage as GitStorage

log = logging.getLogger(__name__)

_github_private_key = None
_github_url = None
_github_history_url = None

GIT_BUSY = asyncio.Event()
GIT_BUSY.set()


class Storage(GitStorage):
    def __init__(self):
        super().__init__()

        # We need to write the private key to disk: GitPython can only use
        # SSH-keys that are written on disk.
        if _github_private_key:
            self._github_private_key_file = tempfile.NamedTemporaryFile()
            self._github_private_key_file.write(_github_private_key)
            self._github_private_key_file.flush()

            self._ssh_command = f"ssh -i {self._github_private_key_file.name}"
        else:
            self._ssh_command = None

    def prepare(self):
        super().prepare()

        # Make sure the origin is set correctly
        if "origin" not in self._git.remotes:
            self._git.create_remote("origin", _github_url)
        origin = self._git.remotes.origin
        if origin.url != _github_url:
            origin.set_url(_github_url)

    def _remove_empty_folders(self, parent_folder):
        removed = False
        for root, folders, files in os.walk(parent_folder, topdown=False):
            if root.startswith(".git"):
                continue

            if not folders and not files:
                os.rmdir(root)
                removed = True

        return removed

    def _fetch_latest(self):
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

    async def _fetch_latest_async(self):
        await GIT_BUSY.wait()
        GIT_BUSY.clear()

        try:
            self._fetch_latest()
        finally:
            GIT_BUSY.set()

    def reload(self):
        super().reload()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._fetch_latest_async())

    async def _push_async(self):
        if not self._ssh_command:
            log.error("No GitHub private key supplied; cannot push to GitHub.")
            return

        await GIT_BUSY.wait()
        GIT_BUSY.clear()

        do_reload = False
        try:
            with self._git.git.custom_environment(GIT_SSH_COMMAND=self._ssh_command):
                self._git.remotes.origin.push()
        except Exception:
            log.exception("Git push failed")
            do_reload = True
            # We cannot do self.reload() here, as GIT_BUSY is taken by us.
            # So first release GIT_BUSY, then do a self.reload().
        finally:
            GIT_BUSY.set()

        if do_reload:
            self.reload()

    def commit(self, user, commit_message):
        super().commit(user, commit_message)

        loop = asyncio.get_event_loop()
        loop.create_task(self._push_async())

    def get_history_url(self, page):
        page = urllib.parse.quote(page)
        return f"{_github_history_url}/commits/master/{page}"

    def get_repository_url(self):
        return _github_history_url


@click_helper.extend
@click.option(
    "--storage-github-url",
    help="Repository URL on GitHub.",
    default="https://github.com/OpenTTD/wiki",
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
