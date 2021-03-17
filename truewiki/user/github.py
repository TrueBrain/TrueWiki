import click

from aiohttp import web
from aioauth_client import GithubClient
from openttd_helpers import click_helper
from typing import Tuple

from .base_oauth2 import User as BaseUser


GITHUB_CLIENT_ID = None
GITHUB_CLIENT_SECRET = None


@click_helper.extend
@click.option("--user-github-client-id", help="GitHub client ID. (user=github only)")
@click.option(
    "--user-github-client-secret",
    help="GitHub client secret. Always use this via an environment variable! (user=github only)",
)
def click_user_github(user_github_client_id, user_github_client_secret):
    global GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

    GITHUB_CLIENT_ID = user_github_client_id
    GITHUB_CLIENT_SECRET = user_github_client_secret


class User(BaseUser):
    routes = web.RouteTableDef()
    method = "github"
    scope = None

    def __init__(self, redirect_uri):
        super().__init__(redirect_uri)

        if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
            raise Exception("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET should be set via environment")

        self._oauth2 = GithubClient(client_id=GITHUB_CLIENT_ID, client_secret=GITHUB_CLIENT_SECRET)

    def get_git_author(self) -> Tuple[str, str]:
        return (self.display_name, f"{self.display_name.lower()}@users.noreply.github.com")

    @staticmethod
    @routes.get("/user/github-callback")
    async def login_github_callback(request):
        return await BaseUser.login_oauth2_callback(request)

    @staticmethod
    def get_description():
        return "Login via GitHub"

    @staticmethod
    def get_settings_url():
        return f"https://github.com/settings/connections/applications/{GITHUB_CLIENT_ID}"
