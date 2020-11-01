import wikitextparser

from wikitexthtml.render import wikilink

from ... import metadata
from ...wiki_page import WikiPage
from ...wrapper import wrap_page


def add_content(page: str) -> str:
    language = page.split("/")[1]

    # List all the categories for this language.
    categories = []
    for category in metadata.CATEGORIES:
        if not category.startswith(f"{language}/"):
            continue

        link = f"<li>[[:Category:{category}]]</li>"
        categories.append(link)

    wtp = wikitextparser.parse("\n".join(sorted(categories, key=lambda x: x.split("/")[-2])))
    wikilink.replace(WikiPage(page), wtp)

    templates = {
        "categories": wtp.string,
    }
    variables = {
        "has_categories": "1",
    }

    return wrap_page(page, "Category", variables, templates)
