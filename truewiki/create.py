import logging

from wikitexthtml.render import wikilink
import wikitextparser

from . import metadata
from .wrapper import wrap_page
from .wiki_page import WikiPage

log = logging.getLogger(__name__)

NAMESPACE_MAPPING = {
    "Template/": ":Template:",
    "Category/": ":Category:",
    "Page/": "",
}


def create_category_index(page):
    templates = set()
    pages = set()
    categories = set()
    other_language = set()

    category_page = page[len("Category/") :]
    language = category_page.split("/")[0]

    for page_in_category in metadata.CATEGORIES.get(category_page, []):
        for namespace, prefix in NAMESPACE_MAPPING.items():
            if not page_in_category.startswith(namespace):
                continue

            page_in_category = page_in_category[len(namespace) :]
            link = f"<li>[[{prefix}{page_in_category}]]</li>"

            if namespace == "Templates/":
                add_func = templates.add
            elif namespace == "Category/":
                add_func = categories.add
            else:
                add_func = pages.add

            break
        else:
            raise RuntimeError(f"{page_in_category} has invalid namespace")

        if page_in_category.split("/")[0] != language:
            other_language.add(link)
        else:
            add_func(link)

    render_templates = {}

    if templates:
        wtp = wikitextparser.parse("\n".join(sorted(templates, key=lambda x: x.split("/")[-2])))
        wikilink.replace(WikiPage(page), wtp)
        render_templates["templates"] = wtp.string

    if categories:
        wtp = wikitextparser.parse("\n".join(sorted(categories, key=lambda x: x.split("/")[-2])))
        wikilink.replace(WikiPage(page), wtp)
        render_templates["categories"] = wtp.string

    if pages:
        wtp = wikitextparser.parse("\n".join(sorted(pages, key=lambda x: x.split("/")[-2])))
        wikilink.replace(WikiPage(page), wtp)
        render_templates["pages"] = wtp.string

    if other_language:
        wtp = wikitextparser.parse("\n".join(sorted(other_language, key=lambda x: x.split("/")[-2])))
        wikilink.replace(WikiPage(page), wtp)
        render_templates["other_language"] = wtp.string

    # Also set a variable to indicate the section is set
    variables = {}
    for name in render_templates:
        variables[f"has_{name}"] = "1"

    return wrap_page(page, "Category", variables, render_templates)


def create_category_bar(page, categories):
    categories_content = set()
    for category in categories:
        label = "/".join(category.split("/")[1:])
        categories_content.add(f"<li>[[:Category:{category}|{label}]]</li>")

    wtp = wikitextparser.parse("\n".join(sorted(categories_content)))
    wikilink.replace(WikiPage(page), wtp)
    return '<div id="categories"><div>Categories:</div><ul>' + wtp.string + "</ul></div>"


def create_language_bar(page, en_page):
    with open("templates/Language.mediawiki", "r") as fp:
        body = fp.read()

    language_content = ""
    for url in metadata.TRANSLATIONS.get(en_page, []):
        if not url.startswith(tuple(NAMESPACE_MAPPING)):
            raise RuntimeError(f"{url} has invalid namespace")

        language = url.split("/")[1]
        if url.startswith("Page/"):
            url = url[len("Page/") :]

        wtp = wikitextparser.parse(body)
        for template in reversed(wtp.templates):
            if template.name == "language":
                template.string = language
            elif template.name == "url":
                template.string = url

        wikilink.replace(WikiPage(page), wtp)
        language_content += wtp.string.strip()

    return language_content
