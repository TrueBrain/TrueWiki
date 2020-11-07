from aiohttp import web

from . import (
    error,
    source,
)
from ..wiki_page import WikiPage


def view(user, page: str, body: str) -> web.Response:
    if page.endswith("/"):
        page += "Main Page"

    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return error.view(user, page, "Error 404 - File not found")

    body = source.create_body(wiki_page, user, "Edit", preview=body)
    return web.Response(body=body, content_type="text/html")
