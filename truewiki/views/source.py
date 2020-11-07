import os
import wikitextparser

from aiohttp import web
from wikitexthtml.render import wikilink

from . import error
from .. import (
    metadata,
    singleton,
)
from ..content import breadcrumb
from ..wiki_page import (
    NAMESPACE_MAPPING,
    WikiPage,
)
from ..wrapper import wrap_page


def create_body(wiki_page, user, wrapper, preview=None) -> str:
    ondisk_name = wiki_page.page_ondisk_name(wiki_page.page)

    if preview:
        body = preview
        wtp = wiki_page.prepare(preview)
        content = wiki_page.render_page(wtp)
    else:
        filename = f"{singleton.STORAGE.folder}/{ondisk_name}"
        if os.path.exists(filename):
            with open(filename) as fp:
                body = fp.read()
        else:
            body = ""

        content = wiki_page.render().html

    templates_used = [f"<li>[[:Template:{template}]]</li>" for template in wiki_page.templates]
    errors = [f"<li>{error}</li>" for error in wiki_page.errors]

    used_on_pages = []
    for dependency in metadata.TEMPLATES[ondisk_name[: -len(".mediawiki")]]:
        namespace = NAMESPACE_MAPPING[dependency.split("/")[0] + "/"]
        dependency = "/".join(dependency.split("/")[1:])
        used_on_pages.append(f"<li>[[{namespace}{dependency}]]</li>")

    wtp = wikitextparser.parse("\n".join(sorted(templates_used)))
    wikilink.replace(wiki_page, wtp)
    templates_used = wtp.string

    wtp = wikitextparser.parse("\n".join(used_on_pages))
    wikilink.replace(wiki_page, wtp)
    used_on_pages = wtp.string

    templates = {
        "content": content,
        "page": body,
        "templates_used": templates_used,
        "used_on_pages": used_on_pages,
        "language": "",
        "footer": "",
        "errors": "\n".join(errors),
        "breadcrumbs": breadcrumb.create(wiki_page.page),
    }
    variables = {
        "has_templates_used": "1" if templates_used else "",
        "has_used_on_pages": "1" if used_on_pages else "",
        "has_errors": "1" if errors else "",
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
        "is_preview": "1" if preview else "",
    }

    templates["language"] = wiki_page.add_language(wiki_page.page)
    templates["footer"] = wiki_page.add_footer(wiki_page.page)
    templates["content"] += wiki_page.add_content(wiki_page.page)

    return wrap_page(wiki_page.page, wrapper, variables, templates)


def view(user, page: str) -> web.Response:
    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return error.view(user, page, "Error 404 - File not found")

    # If there is a difference in case, nicely point this out to users.
    correct_page = wiki_page.page_get_correct_case(page)
    if correct_page != page:
        return error.view(
            user,
            page,
            f'"{page}" does not exist; did you mean [[{correct_page}]]?',
        )

    body = create_body(wiki_page, user, "Source")

    status_code = 200 if wiki_page.page_exists(page) else 404
    return web.Response(body=body, content_type="text/html", status=status_code)
