import wikitextparser

from wikitexthtml.render import wikilink

from ... import metadata
from ...wiki_page import (
    NAMESPACE_MAPPING,
    WikiPage,
)
from ...wrapper import wrap_page


def add_content(page: str) -> str:
    items = {
        "templates": [],
        "pages": [],
        "categories": [],
        "other_language": [],
    }

    category_page = page[len("Category/") :]
    language = category_page.split("/")[0]

    for page_in_category in metadata.CATEGORIES.get(category_page, []):
        for namespace, prefix in NAMESPACE_MAPPING.items():
            if not page_in_category.startswith(namespace):
                continue

            page_in_category = page_in_category[len(namespace) :]
            link = f"<li>[[{prefix}{page_in_category}]]</li>"

            if namespace == "Templates/":
                append = items["templates"].append
            elif namespace == "Category/":
                append = items["categories"].append
            else:
                append = items["pages"].append

            break
        else:
            raise RuntimeError(f"{page_in_category} has invalid namespace")

        if page_in_category.split("/")[0] != language:
            append = items["other_language"].append

        append(link)

    templates = {}
    variables = {}
    for name, values in items.items():
        if values:
            wtp = wikitextparser.parse("\n".join(values))
            wikilink.replace(WikiPage(page), wtp)
            templates[name] = wtp.string
            variables[f"has_{name}"] = "1"

    return wrap_page(page, "Category", variables, templates)
