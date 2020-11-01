import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage


def add_footer(page, prefix):
    folder = "/".join(page.split("/")[:-1])

    if folder.startswith(f"{prefix}/"):
        folder = folder[len(f"{prefix}/") :]

    wtp = wikitextparser.parse(f"[[:Folder:{prefix}/{folder}]]")
    wikilink.replace(WikiPage(page), wtp)
    return f'<div id="folder">Folder: {wtp.string}</div>'
