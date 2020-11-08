import datetime
import secrets

from aiohttp import web

from ..user_session import (
    SESSION_COOKIE_NAME,
    create_bearer_token,
    delete_user,
    handover_to_bearer,
    get_login_expire,
    get_session_expire,
)


class User:
    method = None  # type: str

    def __init__(self, redirect_uri):
        self.redirect_uri = redirect_uri

        self.code = secrets.token_hex(32)
        self.login_expire = datetime.datetime.now() + datetime.timedelta(seconds=get_login_expire())

        self.bearer_token = None
        self.session_expire = None
        self.display_name = None
        self.id = None

    @property
    def full_id(self):
        if self.id is None:
            return None

        return f"{self.method}:{self.id}"

    def is_logged_in(self):
        return self.id is not None

    def logout(self):
        delete_user(self)

    def check_expire(self):
        if self.login_expire and datetime.datetime.now() > self.login_expire:
            self.logout()
            return None

        if self.session_expire and datetime.datetime.now() > self.session_expire:
            self.logout()
            return None

        return self

    def validate(self):
        self.bearer_token = create_bearer_token()
        self.session_expire = datetime.datetime.now() + datetime.timedelta(seconds=get_session_expire())

        handover_to_bearer(self, self.bearer_token)

        self.login_expire = None

        response = web.HTTPFound(location=f"{self.redirect_uri}")
        response.set_cookie(SESSION_COOKIE_NAME, self.bearer_token, max_age=get_session_expire(), httponly=True)
        return response

    def get_git_author(self) -> str:
        raise NotImplementedError()

    def get_authorize_page(self):
        raise NotImplementedError()

    @staticmethod
    def get_description():
        raise NotImplementedError()

    @staticmethod
    def get_settings_url():
        raise NotImplementedError()
