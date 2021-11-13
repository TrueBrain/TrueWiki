import click
import logging
import os
import urllib

from aiohttp import web
from openttd_helpers import click_helper

from . import (
    config,
    singleton,
)
from .views import (
    edit,
    license,
    login,
    source,
    page as view_page,
    preview,
    sitemap,
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


def _validate_page(page: str) -> None:
    # If there is no "/" in the page name, it is a page in the root-folder,
    # and that means we don't have to check for directory traversal.
    if "/" not in page:
        return

    filename = os.path.basename(page)
    path = os.path.normpath(os.path.dirname(page))
    fullpath = f"{path}/{filename}"

    # Don't allow directory traversal
    if fullpath.startswith((".", "/")):
        raise web.HTTPNotFound()

    # If normalization resulted in a different path, redirect to the new path.
    # For example:
    #   /en/./ -> /en/
    #   /en/test/../ -> /en/
    if fullpath != page:
        raise web.HTTPFound(f"/{fullpath}")


@routes.get("/")
@csp_header
async def root(request):
    return web.HTTPFound(f"/{config.PRIMARY_LANGUAGE}/")


@routes.get("/favicon.ico")
async def index(request):
    if not config.FAVICON:
        raise web.HTTPNotFound()

    return web.FileResponse(f"{singleton.STORAGE.folder}{config.FAVICON}")


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

    return web.HTTPNoContent()


@routes.get("/healthz")
@csp_header
async def healthz_handler(request):
    return web.HTTPOk()


@routes.get("/License")
@csp_header
async def license_page(request):
    user = get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME))
    return license.view(user)


@routes.get("/sitemap.xml")
@csp_header
async def sitemap_page(request):
    return sitemap.view()


@routes.get("/robots.txt")
@csp_header
async def robots(request):
    if singleton.FRONTEND_URL:
        return web.Response(
            body=f"User-agent: *\nSitemap: {singleton.FRONTEND_URL}/sitemap.xml",
            content_type="text/plain",
        )
    else:
        return web.Response(body="User-agent: *", content_type="text/plain")


@routes.get("/search")
@csp_header
async def search(request):
    site = singleton.FRONTEND_URL
    if not site:
        return web.HTTPNotFound()

    if site.startswith("http://"):
        site = site[len("http://") :]
    elif site.startswith("https://"):
        site = site[len("https://") :]

    query = request.query.get("query", "")
    if query:
        query += " "

    language = request.query.get("language", "")
    if language:
        language = f"%2F{language}%2F"

    return web.HTTPFound(f"https://duckduckgo.com/?q={query}site%3A{site}{language}")


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
    summary = payload["summary"].replace("\r", "")

    # Make sure summary is not more than 500 chars. This is normally limited
    # by the HTML form itself, so if this is somehow longer, people have
    # been messing with the HTML. We should probably just reject the request
    # at this point.
    if len(summary) > 500:
        raise web.HTTPBadRequest(reason="Summary exceeds maximum length of 500 characters.")

    # Make sure that page names don't contain /../ or anything silly.
    new_page = payload.get("page", page)
    filename = os.path.basename(new_page)
    path = os.path.normpath(os.path.dirname(new_page))
    new_page = f"{path}/{filename}"

    if "save" in payload:
        return edit.save(user, page, new_page, content, payload, summary)

    if "preview" in payload:
        return preview.view(user, page, new_page, content, summary)

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

    if_modified_since = request.if_modified_since
    return view_page.view(user, page, if_modified_since)


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
