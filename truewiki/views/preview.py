from aiohttp import web

from . import (
    error,
    source,
)
from ..wiki_page import WikiPage


def view(user, page: str, new_page: str, body: str) -> web.Response:
    wiki_page = WikiPage(page)
    page_error = wiki_page.page_is_valid(page)
    if page_error:
        return error.view(user, page, page_error)

    body = source.create_body(wiki_page, user, "Edit", preview=body, new_page=new_page)
    return web.Response(body=body, content_type="text/html")
