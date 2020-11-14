import logging
import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage

log = logging.getLogger(__name__)


def link_and_replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target

    if target.startswith(":"):
        target = target[1:]
    target = target[len("template:") :].strip()

    # Generate a link to the language root, which will list all templates
    # of that language.
    # Example: [[:Template:en]]
    if len(target) == 2:
        target += "/Main Page"

    wikilink.target = "Template/" + target
    return False


# [[:Template]] and [[Template]] have the same meaning.
wikilink.register_namespace(":template", link_and_replace)
wikilink.register_namespace("template", link_and_replace)
