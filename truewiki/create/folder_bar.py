import wikitextparser

from wikitexthtml.render import wikilink

from ..wiki_page import WikiPage


def create(page):
    folder = "/".join(page.split("/")[:-1])
    wtp = wikitextparser.parse(f"[[:Folder:{folder}]]")
    wikilink.replace(WikiPage(page), wtp)
    return f'<div id="folder">Page is in folder: {wtp.string}</div>'
