import secrets

from aiohttp import web

from .base import User as BaseUser


_states = {}


def in_query_oauth2_code(code):
    if code is None:
        raise web.HTTPBadRequest(text="code is not set in query-string")

    # This code is sent by OAuth2, and should be at least 20 characters.
    # OAuth2 makes no promises over the length.
    if len(code) < 20:
        raise web.HTTPBadRequest(text="code seems to be an invalid OAuth2 callback code")

    return code


def in_query_oauth2_state(state):
    if state is None:
        raise web.HTTPBadRequest(text="state is not set in query-string")

    # We generated this state with token_hex(16), and as such should always
    # be 32 in length.
    if len(state) != 32:
        raise web.HTTPBadRequest(text="state is not a valid uuid")

    return state


class User(BaseUser):
    scope = None
    _oauth2 = None
    _redirect_uri = None

    def get_authorize_page(self):
        # Chance on collision is really low, but would be really annoying. So
        # simply protect against it by looking for an unused UUID.
        state = secrets.token_hex(16)
        while state in _states:
            state = secrets.token_hex(16)
        self._state = state

        _states[self._state] = self

        kwargs = {
            "state": self._state,
        }
        if self._redirect_uri:
            kwargs["redirect_uri"] = self._redirect_uri
        if self.scope:
            kwargs["scope"] = self.scope

        authorize_url = self._oauth2.get_authorize_url(**kwargs)
        return web.HTTPFound(location=authorize_url)

    @staticmethod
    def get_by_state(state):
        if state not in _states:
            return None

        user = _states[state]
        user._forget_oauth2_state()

        return user

    def logout(self):
        self._forget_oauth2_state()

        super().logout()

    def _forget_oauth2_state(self):
        if self._state:
            del _states[self._state]

        self._state = None

    async def get_user_information(self, code):
        kwargs = {
            "code": code,
        }
        if self._redirect_uri:
            kwargs["redirect_uri"] = self._redirect_uri

        # Validate the code and fetch the user info
        await self._oauth2.get_access_token(**kwargs)
        user, _ = await self._oauth2.user_info()

        self.display_name = user.username
        self.id = str(user.id)

    @staticmethod
    async def login_oauth2_callback(request):
        state = in_query_oauth2_state(request.query.get("state"))
        user = User.get_by_state(state)
        if user is None:
            return web.HTTPNotFound()

        # If "code" is not set, this is most likely a "Cancel" action of the
        # user on the Authorize page. So do the only thing we can do ..
        # redirect the user to the redirect-uri, and let him continue his
        # journey.
        if "code" not in request.query:
            return web.HTTPFound(location=f"{user.redirect_uri}")

        code = in_query_oauth2_code(request.query.get("code"))
        await user.get_user_information(code)
        return user.validate()
