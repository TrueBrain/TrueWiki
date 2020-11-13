import time

from aiohttp import web

from . import error
from .. import metadata
from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def _view(wiki_page, user, page: str) -> web.Response:
    templates = {
        "content": wiki_page.render().html,
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
        "errors": len(wiki_page.errors) if wiki_page.errors else "",
    }

    templates["language"] = wiki_page.add_language(page)
    templates["footer"] = wiki_page.add_footer(page)
    templates["content"] += wiki_page.add_content(page)

    body = wrap_page(page, "Page", variables, templates)

    status_code = 200 if wiki_page.page_exists(page) else 404
    return web.Response(body=body, content_type="text/html", status=status_code)


def view(user, page: str, if_modified_since) -> web.Response:
    if page.endswith("/"):
        page += "Main Page"

    wiki_page = WikiPage(page)
    page_error = wiki_page.page_is_valid(page)
    if page_error:
        return error.view(user, page, page_error)

    # If there is a difference in case, nicely point this out to users.
    correct_page = wiki_page.page_get_correct_case(page)
    if correct_page != page:
        return error.view(
            user,
            page,
            f'"{page}" does not exist; did you mean [[{correct_page}]]?',
        )

    # Check if we already rendered this page before. If the browser has it in
    # his cache, he can simply reuse that if we haven't rendered since.
    if (
        if_modified_since is not None
        and f"Page/{page}" in metadata.LAST_TIME_RENDERED
        and metadata.LAST_TIME_RENDERED[f"Page/{page}"] <= if_modified_since.timestamp()
    ):
        response = web.HTTPNotModified()
    else:
        response = _view(wiki_page, user, page)
        metadata.LAST_TIME_RENDERED[f"Page/{page}"] = time.time()

    # Inform the browser under which rules it can cache this page.
    response.last_modified = metadata.LAST_TIME_RENDERED[f"Page/{page}"]
    response.headers["Vary"] = "Accept-Encoding, Cookie"
    response.headers["Cache-Control"] = "private, must-revalidate, max-age=0"
    return response
