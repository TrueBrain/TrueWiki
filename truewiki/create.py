import logging

from wikitexthtml.render import wikilink
import wikitextparser

from . import metadata
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

    for page_in_category in metadata.CATEGORIES.get(category_page, []):
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
        variables[name] = "1"

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
