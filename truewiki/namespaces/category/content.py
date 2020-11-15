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
        "files": [],
    }

    category_page = page[len("Category/") :]

    for page_in_category in metadata.CATEGORIES.get(category_page, []):
        for namespace, prefix in NAMESPACE_MAPPING.items():
            if not page_in_category.startswith(namespace):
                continue

            page_in_category = page_in_category[len(namespace) :]
            link = f"<li>[[{prefix}{page_in_category}]]</li>"

            if namespace == "Templates/":
                items["templates"].append(link)
            elif namespace == "Category/":
                items["categories"].append(link)
            elif namespace == "File/":
                caption = f'[[:File:{page_in_category}|{page_in_category.split("/")[-1]}]]'
                link = f"<li>[[File:{page_in_category}|none|frame|130px|{caption}]]</li>"
                items["files"].append(link)
            else:
                items["pages"].append(link)

            break
        else:
            raise RuntimeError(f"{page_in_category} has invalid namespace")

    templates = {}
    variables = {}
    for name, values in items.items():
        if values:
            wtp = wikitextparser.parse("\n".join(values))
            wikilink.replace(WikiPage(page), wtp)
            templates[name] = wtp.string
            variables[f"has_{name}"] = "1"

    return wrap_page(page, "snippet/Category", variables, templates)
