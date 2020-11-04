import os
import wikitextparser

from wikitexthtml.render import wikilink

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


def view(user, page: str) -> str:
    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return None

    ondisk_name = wiki_page.page_ondisk_name(page)
    filename = f"{singleton.STORAGE.folder}/{ondisk_name}"
    if os.path.exists(filename):
        with open(filename) as fp:
            body = fp.read()
    else:
        body = ""

    wiki_page.render()

    templates_used = [f"<li>[[:Template:{template}]]</li>" for template in wiki_page.templates]
    errors = [f"<li>{error}</li>" for error in wiki_page.errors]

    used_on_pages = []
    for dependency in metadata.TEMPLATES[ondisk_name[: -len(".mediawiki")]]:
        namespace = NAMESPACE_MAPPING[dependency.split("/")[0] + "/"]
        dependency = "/".join(dependency.split("/")[1:])
        used_on_pages.append(f"<li>[[{namespace}{dependency}]]</li>")

    wtp = wikitextparser.parse("\n".join(sorted(templates_used)))
    wikilink.replace(WikiPage(page), wtp)
    templates_used = wtp.string

    wtp = wikitextparser.parse("\n".join(used_on_pages))
    wikilink.replace(WikiPage(page), wtp)
    used_on_pages = wtp.string

    templates = {
        "page": body,
        "templates_used": templates_used,
        "used_on_pages": used_on_pages,
        "errors": "\n".join(errors),
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "has_templates_used": "1" if templates_used else "",
        "has_used_on_pages": "1" if used_on_pages else "",
        "has_errors": "1" if errors else "",
        "display_name": user.display_name if user else "",
    }

    return wrap_page(page, "Source", variables, templates)
