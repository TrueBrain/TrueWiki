import logging

from wikitexthtml.render import wikilink
import wikitextparser

from .metadata import (
    CATEGORIES,
    TRANSLATIONS,
)
from .wrapper import wrap_page
from .wiki_page import WikiPage

log = logging.getLogger(__name__)

SPECIAL_FOLDERS = ("Template/", "Category/")


def create_category_index(page):
    templates = set()
    pages = set()
    categories = set()
    other_language = set()

    category_page = page[len("Category/") :]
    language = category_page.split("/")[0]

    for page_in_category in CATEGORIES.get(category_page, []):
        if page_in_category.startswith("Template/"):
            page_in_category = page_in_category[len("Template/") :]
            link = f"<li>[[:Template:{page_in_category}]]</li>"
            add_func = templates.add
        elif page_in_category.startswith("Category/"):
            page_in_category = page_in_category[len("Category/") :]
            link = f"<li>[[:Category:{page_in_category}]]</li>"
            add_func = categories.add
        else:
            link = f"<li>[[{page_in_category}]]</li>"
            add_func = pages.add

        if page_in_category.split("/")[0] != language:
            other_language.add(link)
        else:
            add_func(link)

    variables = {}

    wtp = wikitextparser.parse("\n".join(sorted(templates)))
    wikilink.replace(WikiPage(page), wtp)
    variables["templates"] = wtp.string

    wtp = wikitextparser.parse("\n".join(sorted(categories)))
    wikilink.replace(WikiPage(page), wtp)
    variables["categories"] = wtp.string

    wtp = wikitextparser.parse("\n".join(sorted(pages)))
    wikilink.replace(WikiPage(page), wtp)
    variables["pages"] = wtp.string

    wtp = wikitextparser.parse("\n".join(sorted(other_language)))
    wikilink.replace(WikiPage(page), wtp)
    variables["other_language"] = wtp.string

    return wrap_page(page, "Category", variables)


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
    for url in TRANSLATIONS.get(en_page, []):
        if url.startswith(SPECIAL_FOLDERS):
            language = url.split("/")[1]
        else:
            language = url.split("/")[0]

        wtp = wikitextparser.parse(body)
        for template in reversed(wtp.templates):
            if template.name == "language":
                template.string = language
            elif template.name == "url":
                template.string = url

        wikilink.replace(WikiPage(page), wtp)
        language_content += wtp.string.strip()

    return language_content
