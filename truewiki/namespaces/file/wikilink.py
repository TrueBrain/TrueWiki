import html
import logging
import urllib
import wikitextparser

from wikitexthtml.render import wikilink
from wikitexthtml.exceptions import InvalidWikiLink

from ...wiki_page import WikiPage

log = logging.getLogger(__name__)


def link_file(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target[len(":file:") :].strip()

    # Generate a link to the language root, which will list all templates
    # of that language.
    # Example: [[:Template:en]]
    if len(target) == 2:
        target += "/Main Page"

    wikilink.target = "File/" + target
    return False


def link_media(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target
    target = target[len("media:") :].strip()

    url = f"File/{target}"

    text = ""
    # Always run clean_title() on the URL, as it detects URLs that are invalid
    # because of invalid namespaces, etc.
    if url:
        try:
            text = instance.clean_title(url)
        except InvalidWikiLink as e:
            # Errors always end with a dot, hence the [:-1].
            instance.add_error(f'{e.args[0][:-1]} (wikilink "{wikilink.string}").')
            return

    if wikilink.text:
        text = wikilink.text.strip()

    title = html.escape(wikilink.target)
    text = html.escape(text)

    url = instance.clean_url(url)

    if url and not instance.page_exists(url):
        instance.add_error(f'Linked page "{wikilink.title}" does not exist (wikilink "{wikilink.string}").')

        url = f"/{urllib.parse.quote(url)}"
        wikilink.string = f'<a href="{url}" class="new" title="{title}">{title}</a>'
        return True

    if url:
        url = "uploads/" + url[len("File/") :]
        url = f"/{urllib.parse.quote(url)}"

    wikilink.string = f'<a href="{url}" title="{title}">{text}</a>'
    return True


# [[File]] is already handled by wikitexthtml
wikilink.register_namespace(":file", link_file)
wikilink.register_namespace("media", link_media)
