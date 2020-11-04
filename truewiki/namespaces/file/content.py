import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage
from ...wrapper import wrap_page


def add_content(page):
    wtp = wikitextparser.parse(f"[[File:{page[len('File/'):]}|center|link=]]")
    wikilink.replace(WikiPage(page), wtp)
    templates = {"content": wtp.string}

    return wrap_page(page, "File", {}, templates)
