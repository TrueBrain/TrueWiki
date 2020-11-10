import logging
import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage

log = logging.getLogger(__name__)


def replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    # This indicates that the page belongs to this category. We update
    # the WikiPage to indicate this, and otherwise remove the WikiLink.
    category = wikilink.target[len("category:") :]

    error = instance.page_is_valid(f"Category/{category}")
    if error:
        instance.add_error(f'{error[:-1]} (wikilink "{wikilink.string}")')
        return True

    instance.categories.append(category)
    wikilink.string = ""
    return True


def link(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target[len(":category:") :]

    # Generate a link to the language root, which will list all categories
    # of that language.
    # Example: [[:Category:en]]
    if len(target) == 2:
        target += "/Main Page"

    # Tell the target what the URL is to find this category, and let the
    # normal WikiLink handler take care of making that into a link.
    wikilink.target = "Category/" + target
    return False


wikilink.register_namespace(":category", link)
wikilink.register_namespace("category", replace)
