import logging
import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage

log = logging.getLogger(__name__)


def link(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target
    target = target[len(":file:") :]

    # Generate a link to the language root, which will list all templates
    # of that language.
    # Example: [[:Template:en]]
    if len(target) == 2:
        target += "/Main Page"

    wikilink.target = "File/" + target
    return False


# [[:Template]] and [[Template]] have the same meaning.
wikilink.register_namespace(":file", link)
