import wikitextparser

from aiohttp import web
from wikitexthtml.render import wikilink

from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def view(user, page: str, message: str, status: int = 404) -> web.Response:
    wiki_page = WikiPage(page)

    variables = {
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
    }

    wtp = wikitextparser.parse(message)
    wikilink.replace(wiki_page, wtp)

    templates = {
        "content": wtp.string,
        "breadcrumbs": breadcrumb.create(page),
    }
    body = wrap_page(page, "Error", variables, templates)
    return web.Response(body=body, content_type="text/html", status=status)
