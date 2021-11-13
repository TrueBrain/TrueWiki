import click

from aiohttp import web
from aioauth_client import MicrosoftClient
from openttd_helpers import click_helper
from typing import Tuple

from .base_oauth2 import User as BaseUser


MICROSOFT_CLIENT_ID = None
MICROSOFT_CLIENT_SECRET = None


@click_helper.extend
@click.option("--user-microsoft-client-id", help="Microsoft client ID. (user=microsoft only)")
@click.option(
    "--user-microsoft-client-secret",
    help="Microsoft client secret. Always use this via an environment variable! (user=microsoft only)",
)
def click_user_microsoft(user_microsoft_client_id, user_microsoft_client_secret):
    global MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET

    MICROSOFT_CLIENT_ID = user_microsoft_client_id
    MICROSOFT_CLIENT_SECRET = user_microsoft_client_secret


class User(BaseUser):
    routes = web.RouteTableDef()
    method = "microsoft"
    scope = "https://graph.microsoft.com/User.Read"

    def __init__(self, redirect_uri):
        super().__init__(redirect_uri)

        if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
            raise Exception("MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET should be set via environment")

        self._oauth2 = MicrosoftClient(client_id=MICROSOFT_CLIENT_ID, client_secret=MICROSOFT_CLIENT_SECRET)

    def get_git_author(self) -> Tuple[str, str]:
        # Microsoft doesn't supply anonymous email address to refer to a user.
        return (self.display_name, self.email)

    @staticmethod
    @routes.get("/user/microsoft-callback")
    async def login_microsoft_callback(request):
        return await BaseUser.login_oauth2_callback(request)

    @staticmethod
    def get_description():
        return "Login via Microsoft"

    @staticmethod
    def get_settings_url():
        # Microsoft doesn't appear to have a single settings page to revoke app permissions.
        return ""
