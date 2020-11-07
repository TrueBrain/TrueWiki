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

    # If there is a difference in case, nicely point this out to users.
    correct_page = wiki_page.page_get_correct_case(page)
    if correct_page != page:
        return error.view(
            user,
            page,
            f'Page name "{page}" conflicts with "{correct_page}". Did you mean to preview [[{correct_page}]]?',
        )

    body = source.create_body(wiki_page, user, "Edit", {"is_preview": "1"})
    return web.Response(body=body, content_type="text/html")
