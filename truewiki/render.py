import wikitextparser

from wikitexthtml.render import wikilink

from .create import (
    create_category_bar,
    create_category_index,
    create_language_bar,
)
from .wiki_page import WikiPage
from .wrapper import wrap_page


def render_source(page: str) -> str:
    body = WikiPage(page).page_load(page)
    wtp = wikitextparser.parse(body)

    templates_used = set()
    for template in wtp.templates:
        templates_used.add(f"<li>[[:Template:{template.name}]]</li>")

    wtp = wikitextparser.parse("\n".join(sorted(list(templates_used))))
    wikilink.replace(WikiPage(page), wtp)
    templates_used = wtp.string

    variables = {
        "content": body,
        "templates_used": templates_used,
    }

    return wrap_page(page, "Source", variables)


def render_page(page: str) -> str:
    if page.endswith("/"):
        page += "Main Page"

    wikipage = WikiPage(page)

    variables = {
        "content": wikipage.render().html,
        "language": "",
        "category": "",
    }

    if wikipage.en_page:
        variables["language"] = create_language_bar(page, wikipage.en_page)
    if wikipage.categories:
        variables["category"] = create_category_bar(page, wikipage.categories)

    if page.startswith("Category/"):
        variables["content"] += create_category_index(page)

    return wrap_page(page, "Page", variables)
