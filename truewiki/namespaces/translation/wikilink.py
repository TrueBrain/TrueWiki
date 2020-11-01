import logging
import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage

log = logging.getLogger(__name__)


def replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    page = wikilink.target[len("translation:") :]

    # Mark what the English page is this translation is based on.
    instance.en_page = page

    wikilink.string = ""
    return True


# We do not support [[:translation]] as it has no meaning.
wikilink.register_namespace("translation", replace)
