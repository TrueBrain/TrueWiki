import logging
import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage

log = logging.getLogger(__name__)


def link(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target[len(":folder:") :].strip()

    # As we are browsing folders, [[Folder:en]] and [[Folder:en/]] are
    # identical in meaning.
    if not target.endswith("/"):
        target += "/"
    target += "Main Page"

    wikilink.target = "Folder/" + target
    return False


wikilink.register_namespace(":folder", link)
# We do not support [[Folder]] as it has no meaning.
