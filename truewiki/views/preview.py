from aiohttp import web

from . import (
    error,
    source,
)
from ..wiki_page import WikiPage


def view(user, old_page: str, new_page: str, body: str, summary: str = None, has_edit_conflict=False) -> web.Response:
    wiki_page = WikiPage(old_page)
    page_error = wiki_page.page_is_valid(old_page, is_new_page=True)
    if page_error:
        return error.view(user, old_page, page_error)

    if new_page.endswith("/"):
        page_error = (
            f'Page name "{new_page}" cannot end with a "/". If you meant the main page, please add "Main Page". '
            'The name of the page "Main Page" cannot be translated, and is always written in English, '
            "no matter the language you are in. The content of course can be translated."
        )
    else:
        page_error = wiki_page.page_is_valid(new_page, is_new_page=True)

    body = source.create_body(
        wiki_page,
        user,
        "Edit",
        preview=body,
        summary=summary,
        new_page=new_page,
        page_error=page_error,
        has_edit_conflict=has_edit_conflict,
    )
    return web.Response(body=body, content_type="text/html")
