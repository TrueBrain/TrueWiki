import click
import logging

from aiohttp import web
from openttd_helpers import click_helper

from . import singleton
from .metadata import load_metadata
from .render import (
    render_edit,
    render_login,
    render_source,
    render_page,
    render_preview,
    save_edit,
)
from .user_session import (
    SESSION_COOKIE_NAME,
    get_user_by_bearer,
)

log = logging.getLogger(__name__)
routes = web.RouteTableDef()

RELOAD_SECRET = None


@routes.get("/")
async def root(request):
    return web.HTTPFound("/en/")


@routes.get("/user/login")
async def user_login(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))

    body = render_login(user)
    return web.Response(body=body, content_type="text/html")


@routes.get("/edit/{page:.*}")
async def edit_page(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        return web.HTTPFound("/user/login")

    page = request.match_info["page"]
    # Don't allow path-walking
    if ".." in page:
        raise web.HTTPNotFound()

    body = render_edit(user, page)
    return web.Response(body=body, content_type="text/html")


@routes.post("/edit/{page:.*}")
async def edit_page_post(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        return web.HTTPFound("/user/login")

    page = request.match_info["page"]
    # Don't allow path-walking
    if ".." in page:
        raise web.HTTPNotFound()

    payload = await request.post()
    if "page" not in payload:
        raise web.HTTPNotFound()

    # TODO -- Check if the page is created in a legal place

    if "save" in payload:
        save_edit(user, page, payload["page"])
        return web.HTTPFound(f"/{page}")

    if "preview" in payload:
        body = render_preview(user, page, payload["page"])
        return web.Response(body=body, content_type="text/html")

    raise web.HTTPNotFound()


@routes.get("/{page:.*}.mediawiki")
async def source_page(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))

    page = request.match_info["page"]
    # Don't allow path-walking
    if ".." in page:
        raise web.HTTPNotFound()

    body = render_source(user, page)
    return web.Response(body=body, content_type="text/html")


@routes.get("/{page:.*}")
async def html_page(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))

    page = request.match_info["page"]
    # Don't allow path-walking
    if ".." in page:
        raise web.HTTPNotFound()

    body = render_page(user, page)
    return web.Response(body=body, content_type="text/html")


@routes.post("/reload")
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
async def healthz_handler(request):
    return web.HTTPOk()


@routes.route("*", "/{tail:.*}")
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
