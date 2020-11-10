import wikitextparser

from wikitexthtml.render import wikilink

from ... import singleton
from ...wiki_page import WikiPage
from ...wrapper import wrap_page


def add_content(page, namespace="Folder", namespace_for_folder=False, folder_label="Folders", page_label="Pages"):
    items = {
        "pages": [],
        "folders": [],
    }

    if not page.endswith("/Main Page"):
        return ""

    folder = page[len("Folder/") : -len("/Main Page")]

    for item in sorted(singleton.STORAGE.dir_listing(folder)):
        if singleton.STORAGE.dir_exists(item):
            if namespace != "Folder" and (len(item.split("/")) == 2 or namespace_for_folder):
                item = item[len(f"{namespace}/") :]
                items["folders"].append(f"<li>[[:{namespace}:{item}/Main Page]]</li>")
                continue

            items["folders"].append(f"<li>[[:Folder:{item}]]</li>")
            continue

        if item.endswith(".mediawiki"):
            if namespace != "Folder":
                item = item[len(f"{namespace}/") :]
            item = item[: -len(".mediawiki")]

            if namespace == "Folder":
                # Special case; in the repository it is called
                # LICENSE.mediawiki, but we call it "License" everywhere
                # else.
                if item == "LICENSE":
                    item = "License"
                if item.startswith("Page/"):
                    item = item[len("Page/") :]

                items["pages"].append(f"<li>[[{item}]]</li>")
                continue

            items["pages"].append(f"<li>[[:{namespace}:{item}]]</li>")
            continue

    templates = {}
    variables = {
        "folder_label": folder_label,
        "page_label": page_label,
    }
    for name, values in items.items():
        if values:
            wtp = wikitextparser.parse("\n".join(sorted(values, key=lambda x: x.split("/")[-2])))
            wikilink.replace(WikiPage(page), wtp)
            templates[name] = wtp.string
            variables[f"has_{name}"] = "1"

    return wrap_page(page, "Folder", variables, templates)
