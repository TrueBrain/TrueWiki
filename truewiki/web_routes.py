import click
import logging
import regex
import urllib

from aiohttp import web
from openttd_helpers import click_helper

from . import singleton
from .metadata import load_metadata
from .views import (
    edit,
    license as license_page,
    login,
    source,
    page as view_page,
    preview,
)
from .user_session import (
    SESSION_COOKIE_NAME,
    get_user_by_bearer,
)

log = logging.getLogger(__name__)
routes = web.RouteTableDef()

RELOAD_SECRET = None


def csp_header(func):
    async def wrapper(*args, **kwargs):
        response = await func(*args, **kwargs)
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'"
        return response

    return wrapper


@routes.get("/")
@csp_header
async def root(request):
    return web.HTTPFound("/en/")


@routes.get("/user/login")
@csp_header
async def user_login(request):
    location = request.query.get("location")

    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))
    if user:
        if not location:
            location = ""
        return web.HTTPFound(location=f"/{location}")

    body = login.view(user, location=location)
    return web.Response(body=body, content_type="text/html")


@routes.post("/reload")
@csp_header
async def reload(request):
    if RELOAD_SECRET is None:
        return web.HTTPNotFound()

    data = await request.json()

    if "secret" not in data:
        return web.HTTPNotFound()

    if data["secret"] != RELOAD_SECRET:
        return web.HTTPNotFound()

    singleton.STORAGE.reload()
    load_metadata()

    return web.HTTPNoContent()


@routes.get("/healthz")
@csp_header
async def healthz_handler(request):
    return web.HTTPOk()


@routes.get("/License")
@csp_header
async def license(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))
    return license_page.view(user)


def _validate_page(page: str) -> None:
    # Don't allow path-walking
    if ".." in page:
        raise web.HTTPNotFound()

    if "//" in page:
        page = regex.sub(r"//+", "/", page)
        raise web.HTTPFound(f"/{page}")


@routes.get("/edit/{page:.*}")
@csp_header
async def edit_page(request):
    page = request.match_info["page"]
    _validate_page(page)

    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        location = urllib.parse.quote(page)
        return web.HTTPFound(f"/user/login?location=edit/{location}")

    return edit.view(user, page)


@routes.post("/edit/{page:.*}")
@csp_header
async def edit_page_post(request):
    page = request.match_info["page"]
    _validate_page(page)

    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        location = urllib.parse.quote(page)
        return web.HTTPFound(f"/user/login?location=edit/{location}")

    payload = await request.post()
    if "content" not in payload:
        raise web.HTTPNotFound()
    content = payload["content"].replace("\r", "")

    if "save" in payload:
        return edit.save(user, page, payload.get("page", page), content, payload)

    if "preview" in payload:
        return preview.view(user, page, payload.get("page", page), content)

    raise web.HTTPNotFound()


@routes.get("/{page:.*}.mediawiki")
@csp_header
async def source_page(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))

    page = request.match_info["page"]
    _validate_page(page)

    return source.view(user, page)


@routes.get("/{page:.*}")
@csp_header
async def html_page(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))

    page = request.match_info["page"]
    _validate_page(page)

    return view_page.view(user, page)


@routes.route("*", "/{tail:.*}")
@csp_header
async def fallback(request):
    log.warning("Unexpected URL: %s", request.url)
    return web.HTTPNotFound()


@click_helper.extend
@click.option(
    "--reload-secret",
    help="Secret to allow an index reload. Always use this via an environment variable!",
)
def click_web_routes(reload_secret):
    global RELOAD_SECRET

    RELOAD_SECRET = reload_secret
