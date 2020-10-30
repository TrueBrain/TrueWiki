import wikitextparser

from wikitexthtml.render import wikilink

from .create import (
    breadcrumb,
    category_bar,
    category_index,
    folder_bar,
    folder_index,
    language_bar,
)
from .wiki_page import WikiPage
from .wrapper import wrap_page


def render_source(page: str) -> str:
    body = WikiPage(page).page_load(page)
    wikipage = WikiPage(page).render()

    templates_used = [f"<li>[[:Template:{template}]]</li>" for template in wikipage.templates]
    errors = [f"<li>{error}</li>" for error in wikipage.errors]

    wtp = wikitextparser.parse("\n".join(sorted(templates_used)))
    wikilink.replace(WikiPage(page), wtp)
    templates_used = wtp.string

    templates = {
        "content": body,
        "templates_used": templates_used,
        "errors": "\n".join(errors),
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "has_templates_used": "1" if templates_used else "",
        "has_errors": "1" if errors else "",
    }

    return wrap_page(page, "Source", variables, templates)


def render_page(page: str) -> str:
    if page.endswith("/"):
        page += "Main Page"

    wikipage = WikiPage(page)

    templates = {
        "content": wikipage.render().html,
        "language": "",
        "footer": "",
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {}
    if len(wikipage.errors):
        variables["errors"] = len(wikipage.errors)

    if wikipage.en_page:
        templates["language"] = language_bar.create(page, wikipage.en_page)
    if wikipage.categories:
        templates["footer"] += category_bar.create(page, wikipage.categories)

    if page.startswith("Category/"):
        templates["content"] += category_index.create(page)
    elif page.startswith("Folder/"):
        templates["content"] += folder_index.create(page)
    else:
        templates["footer"] += folder_bar.create(page)

    return wrap_page(page, "Page", variables, templates)
