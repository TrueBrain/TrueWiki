from aiohttp import web

from . import error
from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


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

    wtp = wiki_page.prepare(body)
    content = wiki_page.render_page(wtp)
    errors = [f"<li>{error}</li>" for error in wiki_page.errors]

    templates = {
        "content": content,
        "page": body,
        "language": "",
        "footer": "",
        "errors": "\n".join(errors),
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
        "has_errors": "1" if errors else "",
    }

    templates["language"] = wiki_page.add_language(page)
    templates["footer"] = wiki_page.add_footer(page)
    templates["content"] += wiki_page.add_content(page)

    body = wrap_page(page, "Preview", variables, templates)

    return web.Response(body=body, content_type="text/html")
