import click

from aiohttp import web
from aioauth_client import GitlabClient
from openttd_helpers import click_helper
from typing import Tuple

from .base_oauth2 import User as BaseUser
from .. import singleton


GITLAB_CLIENT_ID = None
GITLAB_CLIENT_SECRET = None


@click_helper.extend
@click.option("--user-gitlab-client-id", help="Gitlab client ID. (user=gitlab only)")
@click.option(
    "--user-gitlab-client-secret",
    help="Gitlab client secret. Always use this via an environment variable! (user=gitlab only)",
)
def click_user_gitlab(user_gitlab_client_id, user_gitlab_client_secret):
    global GITLAB_CLIENT_ID, GITLAB_CLIENT_SECRET

    GITLAB_CLIENT_ID = user_gitlab_client_id
    GITLAB_CLIENT_SECRET = user_gitlab_client_secret


class User(BaseUser):
    routes = web.RouteTableDef()
    method = "gitlab"
    scope = "read_user"

    def __init__(self, redirect_uri):
        super().__init__(redirect_uri)

        if not GITLAB_CLIENT_ID or not GITLAB_CLIENT_SECRET:
            raise Exception("GITLAB_CLIENT_ID and GITLAB_CLIENT_SECRET should be set via environment")
        if not singleton.FRONTEND_URL:
            raise Exception("--frontend-url is not set, but is required for GitLab user backend")

        self._oauth2 = GitlabClient(client_id=GITLAB_CLIENT_ID, client_secret=GITLAB_CLIENT_SECRET)
        self._redirect_uri = f"{singleton.FRONTEND_URL}/user/gitlab-callback"

    def get_git_author(self) -> Tuple[str, str]:
        return (self.display_name, f"{self.id}-{self.display_name.lower()}@users.noreply.gitlab.com")

    @staticmethod
    @routes.get("/user/gitlab-callback")
    async def login_gitlab_callback(request):
        return await BaseUser.login_oauth2_callback(request)

    @staticmethod
    def get_description():
        return "Login via Gitlab"

    @staticmethod
    def get_settings_url():
        return "https://gitlab.com/-/profile/applications"
