import glob
import os
import wikitextparser

from wikitexthtml.render import wikilink

from .. import singleton
from ..wrapper import wrap_page
from ..wiki_page import WikiPage

NAMESPACE_MAPPING = {
    "Template/": ":Template:",
    "Category/": ":Category:",
    "Page/": "",
}


def create(page, namespace="Folder"):
    pages = set()
    folders = set()

    if not page.endswith("/Main Page"):
        return ""

    folder = page[len("Folder/") : -len("/Main Page")]

    for item in sorted(glob.glob(f"{singleton.STORAGE.folder}/{folder}/*")):
        item_page = item[len(f"{singleton.STORAGE.folder}/") :]
        if item_page.startswith(f"{namespace}/"):
            item_page = item_page[len(f"{namespace}/") :]

        if os.path.isdir(item):
            folders.add(f"<li>[[:{namespace}:{item_page}]]</li>")
        elif item.endswith(".mediawiki"):
            item_page = item_page[: -len(".mediawiki")]
            if item_page.startswith("Page/"):
                item_page = item_page[len("Page/") :]
            pages.add(f"<li>[[{item_page}]]</li>")

    render_templates = {}

    if folders:
        wtp = wikitextparser.parse("\n".join(sorted(folders, key=lambda x: x.split("/")[-2])))
        wikilink.replace(WikiPage(page), wtp)
        render_templates["folders"] = wtp.string

    if pages:
        wtp = wikitextparser.parse("\n".join(sorted(pages, key=lambda x: x.split("/")[-2])))
        wikilink.replace(WikiPage(page), wtp)
        render_templates["pages"] = wtp.string

    # Also set a variable to indicate the section is set
    variables = {}
    for name in render_templates:
        variables[f"has_{name}"] = "1"

    return wrap_page(page, "Folder", variables, render_templates)
