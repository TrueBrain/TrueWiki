import logging

from aiohttp import web

from .render import (
    render_source,
    render_page,
)

log = logging.getLogger(__name__)
routes = web.RouteTableDef()


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


@routes.route("*", "/{tail:.*}")
async def fallback(request):
    log.warning("Unexpected URL: %s", request.url)
    return web.HTTPNotFound()
