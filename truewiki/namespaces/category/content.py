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
        "templates": set(),
        "pages": set(),
        "categories": set(),
        "other_language": set(),
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
                add_func = items["templates"].add
            elif namespace == "Category/":
                add_func = items["categories"].add
            else:
                add_func = items["pages"].add

            break
        else:
            raise RuntimeError(f"{page_in_category} has invalid namespace")

        if page_in_category.split("/")[0] != language:
            items["other_language"].add(link)
        else:
            add_func(link)

    templates = {}
    variables = {}
    for name, values in items.items():
        if values:
            wtp = wikitextparser.parse("\n".join(sorted(values, key=lambda x: x.split("/")[-2])))
            wikilink.replace(WikiPage(page), wtp)
            templates[name] = wtp.string
            variables[f"has_{name}"] = "1"

    return wrap_page(page, "Category", variables, templates)
