from aiohttp import web

from .. import singleton
from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def view(user) -> web.Response:
    body = singleton.STORAGE.file_read("LICENSE.mediawiki")

    wiki_page = WikiPage("License")
    wtp = wiki_page.prepare(body)

    templates = {
        "content": wiki_page.render_page(wtp),
        "breadcrumbs": breadcrumb.create(""),
        "language": "",
        "footer": "",
    }
    variables = {
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
    }

    body = wrap_page("License", "Page", variables, templates)
    return web.Response(body=body, content_type="text/html")
