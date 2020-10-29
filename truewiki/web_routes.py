import click
import logging

from aiohttp import web
from openttd_helpers import click_helper

from .metadata import load_metadata
from .render import (
    render_source,
    render_page,
)

log = logging.getLogger(__name__)
routes = web.RouteTableDef()

RELOAD_SECRET = None
STORAGE = None


@routes.get("/")
async def root(request):
    return web.HTTPFound("/en/Main Page")


@routes.get("/{page:.*}.mediawiki")
async def source_page(request):
    page = request.match_info["page"]
    # Don't allow path-walking
    if ".." in page:
        raise web.HTTPNotFound()

    body = render_source(page)
    return web.Response(body=body, content_type="text/html")


@routes.get("/{page:.*}")
async def html_page(request):
    page = request.match_info["page"]
    # Don't allow path-walking
    if ".." in page:
        raise web.HTTPNotFound()

    body = render_page(page)

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

    STORAGE.reload()
    load_metadata(STORAGE.folder)

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
