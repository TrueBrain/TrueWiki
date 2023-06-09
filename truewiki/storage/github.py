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

_github_deploy_key = None
_github_url = None
_github_history_url = None
_github_branch = None
_github_app_id = None
_github_app_key = None


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

        git_env = {}
        if self._ssh_command:
            git_env["GIT_SSH_COMMAND"] = self._ssh_command
        elif self._ask_pass:
            git_env["GIT_ASKPASS"] = self._ask_pass

        # Checkout the latest default branch, removing and commits/file
        # changes local might have.
        with self._git.git.custom_environment(**git_env):
            try:
                origin.fetch()
            except git.exc.BadName:
                # When the garbage collector kicks in, GitPython gets confused and
                # throws a BadName. The best solution? Just run it again.
                origin.fetch()

        if branch in origin.refs:
            origin.refs[branch].checkout(force=True, B=branch)
        else:
            branch = self._git.create_head(branch)
            branch.checkout()

        for file_name in self._git.untracked_files:
            os.unlink(f"{self._folder}/{file_name}")

        # We might end up with empty folders, which the rest of the
        # application doesn't really like. So remove them. Keep repeating the
        # function until no folders are removed anymore.
        while self._remove_empty_folders(self._folder):
            pass

        return True

    def push(self, branch):
        git_env = {}
        if self._ssh_command:
            git_env["GIT_SSH_COMMAND"] = self._ssh_command
        elif self._ask_pass:
            git_env["GIT_ASKPASS"] = self._ask_pass

        try:
            with self._git.git.custom_environment(**git_env):
                self._git.remotes.origin.push(f"{branch}:{branch}")
        except Exception:
            log.exception(f"Git push failed; reloading from {self.name}")
            return False

        return True


class Storage(GitStorage):
    out_of_process_class = OutOfProcessStorage

    def __init__(self):
        if _github_deploy_key:
            # We need to write the private key to disk: GitPython can only use
            # SSH-keys that are written on disk.
            self._github_deploy_key_file = tempfile.NamedTemporaryFile()
            self._github_deploy_key_file.write(_github_deploy_key)
            self._github_deploy_key_file.flush()

            super().__init__(ssh_command=f"ssh -i {self._github_deploy_key_file.name}")
        elif _github_app_id and _github_app_key:
            super().__init__(ask_pass=os.path.join(os.path.dirname(__file__), "github-askpass.py"))
        else:
            log.info("Neither a GitHub Deploy key nor a GitHub App is provided")
            log.info("Please make sure you have a credential helper configured for this repository.")
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
        self._run_out_of_process(None, "push", _github_branch)

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
    "--storage-github-deploy-key",
    "--storage-github-private-key",  # Deprecated; use --storage-github-deploy-key instead.
    help="Base64-encoded GitHub Deploy key to access the repository. Use either this or a GitHub App. "
    "Always use this via an environment variable!",
)
@click.option(
    "--storage-github-app-id",
    help="GitHub App ID that has write access to the repository. Use either this or a GitHub Deploy Key.",
)
@click.option(
    "--storage-github-app-key",
    help="Base64-encoded GitHub App Private Key. Use either this or a GitHub Deploy Key. "
    "Always use this via an environment variable!",
)
@click.option(
    "--storage-github-api-url",
    help="GitHub API URL to use with GitHub App.",
    default="https://api.github.com",
    show_default=True,
    metavar="URL",
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
    storage_github_deploy_key,
    storage_github_app_id,
    storage_github_app_key,
    storage_github_api_url,
    storage_github_branch,
):
    global _github_url, _github_history_url, _github_deploy_key, _github_branch, _github_app_id, _github_app_key

    if storage_github_history_url is None:
        storage_github_history_url = storage_github_url

    # Make sure we remain backwards compatible with the old option name.
    if not storage_github_deploy_key and os.getenv("TRUEWIKI_STORAGE_GITHUB_PRIVATE_KEY"):
        storage_github_deploy_key = os.getenv("TRUEWIKI_STORAGE_GITHUB_PRIVATE_KEY")

    _github_url = storage_github_url
    _github_history_url = storage_github_history_url
    _github_branch = storage_github_branch
    if storage_github_deploy_key:
        _github_deploy_key = base64.b64decode(storage_github_deploy_key)
    elif storage_github_app_id and storage_github_app_key:
        # Make sure we can base64 decode it, but we keep the base64 encoded value.
        base64.b64decode(storage_github_app_key)

        _github_app_id = storage_github_app_id
        _github_app_key = storage_github_app_key

        # Use the environment to pass information to the ask-pass script.
        # This way things like the key are never visible in the process list.
        os.environ["TRUEWIKI_GITHUB_ASKPASS_APP_ID"] = _github_app_id
        os.environ["TRUEWIKI_GITHUB_ASKPASS_APP_KEY"] = _github_app_key
        os.environ["TRUEWIKI_GITHUB_ASKPASS_URL"] = _github_url
        os.environ["TRUEWIKI_GITHUB_ASKPASS_API_URL"] = storage_github_api_url
