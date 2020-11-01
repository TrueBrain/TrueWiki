import glob
import os
import wikitextparser

from wikitexthtml.render import wikilink

from ... import singleton
from ...wiki_page import WikiPage
from ...wrapper import wrap_page


def add_content(page, namespace="Folder"):
    items = {
        "pages": set(),
        "folders": set(),
    }

    if not page.endswith("/Main Page"):
        return ""

    folder = page[len("Folder/") : -len("/Main Page")]

    for item in sorted(glob.glob(f"{singleton.STORAGE.folder}/{folder}/*")):
        item_page = item[len(f"{singleton.STORAGE.folder}/") :]

        if os.path.isdir(item):
            if namespace != "Folder" and len(item_page.split("/")) == 2:
                item_page = item_page[len(f"{namespace}/") :]
                items["folders"].add(f"<li>[[:{namespace}:{item_page}]]</li>")
                continue

            items["folders"].add(f"<li>[[:Folder:{item_page}]]</li>")
            continue

        if item.endswith(".mediawiki"):
            if namespace != "Folder":
                item_page = item_page[len(f"{namespace}/") :]
            item_page = item_page[: -len(".mediawiki")]

            if namespace == "Folder":
                if item_page.startswith("Page/"):
                    item_page = item_page[len("Page/") :]
                items["pages"].add(f"<li>[[{item_page}]]</li>")
                continue

            items["pages"].add(f"<li>[[:{namespace}:{item_page}]]</li>")
            continue

    templates = {}
    variables = {}
    for name, values in items.items():
        if values:
            wtp = wikitextparser.parse("\n".join(sorted(values, key=lambda x: x.split("/")[-2])))
            wikilink.replace(WikiPage(page), wtp)
            templates[name] = wtp.string
            variables[f"has_{name}"] = "1"

    return wrap_page(page, "Folder", variables, templates)
