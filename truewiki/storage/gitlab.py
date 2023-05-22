import base64
import click
import logging
import tempfile
import urllib

from openttd_helpers import click_helper

from .git import Storage as GitStorage
from .github import OutOfProcessStorage as GitHubOutOfProcessStorage

log = logging.getLogger(__name__)

_gitlab_private_key = None
_gitlab_url = None
_gitlab_history_url = None
_gitlab_branch = None


class OutOfProcessStorage(GitHubOutOfProcessStorage):
    name = "GitLab"


class Storage(GitStorage):
    out_of_process_class = OutOfProcessStorage

    def __init__(self):
        if _gitlab_private_key:
            # We need to write the private key to disk: GitPython can only use
            # SSH-keys that are written on disk.
            self._gitlab_private_key_file = tempfile.NamedTemporaryFile()
            self._gitlab_private_key_file.write(_gitlab_private_key)
            self._gitlab_private_key_file.flush()

            super().__init__(ssh_command=f"ssh -i {self._gitlab_private_key_file.name}")
        else:
            super().__init__()

    def prepare(self):
        _git = super().prepare()

        # Make sure the origin is set correctly
        if "origin" not in _git.remotes:
            _git.create_remote("origin", _gitlab_url)
        origin = _git.remotes.origin
        if origin.url != _gitlab_url:
            origin.set_url(_gitlab_url)

        return _git

    def reload(self):
        self._run_out_of_process(self._reload_done, "fetch_latest", _gitlab_branch)

    def _reload_done(self):
        super().reload()

    def commit_done(self):
        super().commit_done()
        self._run_out_of_process(None, "push", _gitlab_branch)

    def get_history_url(self, page):
        page = urllib.parse.quote(page)
        return f"{_gitlab_history_url}/-/commits/{_gitlab_branch}/{page}"

    def get_repository_url(self):
        return _gitlab_history_url


@click_helper.extend
@click.option(
    "--storage-gitlab-url",
    help="Repository URL on Gitlab.",
    default="https://gitlab.com/TrueBrain/wiki-example.git/",
    show_default=True,
    metavar="URL",
)
@click.option(
    "--storage-gitlab-history-url",
    help="Repository URL on Gitlab to visit history (defaults to --storage-gitlab-url).",
    default=None,
    show_default=True,
    metavar="URL",
)
@click.option(
    "--storage-gitlab-private-key",
    help="Base64-encoded private key to access Gitlab. Always use this via an environment variable!",
)
@click.option(
    "--storage-gitlab-branch",
    help="Branch of the Gitlab repository to use.",
    default="main",
    show_default=True,
    metavar="branch",
)
def click_storage_gitlab(
    storage_gitlab_url,
    storage_gitlab_history_url,
    storage_gitlab_private_key,
    storage_gitlab_branch,
):
    global _gitlab_url, _gitlab_history_url, _gitlab_private_key, _gitlab_branch

    if storage_gitlab_history_url is None:
        storage_gitlab_history_url = storage_gitlab_url
    # Normally GitLab URLs end on ".git/"; so be nice, and replace that to become a valid URL for humans.
    if storage_gitlab_history_url.endswith(".git/"):
        storage_gitlab_history_url = storage_gitlab_history_url[:-5] + "/"

    _gitlab_url = storage_gitlab_url
    _gitlab_history_url = storage_gitlab_history_url
    _gitlab_branch = storage_gitlab_branch
    if storage_gitlab_private_key:
        _gitlab_private_key = base64.b64decode(storage_gitlab_private_key)
