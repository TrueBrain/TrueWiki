import logging
import wikitextparser

from wikitexthtml.render import wikilink

from .wiki_page import WikiPage

log = logging.getLogger(__name__)


def category_replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    category = wikilink.target[len("category:") :]
    instance.categories.append(category)
    wikilink.string = ""
    return True


def category_link_replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target[len(":category:") :]

    wikilink.target = "Category/" + target
    return False


def folder_link_replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target[len(":folder:") :]

    wikilink.target = "Folder/" + target
    return False


def template_replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    target = wikilink.target

    if target.startswith(":"):
        target = target[1:]
    target = target[len("template:") :]

    wikilink.target = "Template/" + target
    return False


def translation_replace(instance: WikiPage, wikilink: wikitextparser.WikiLink):
    page = wikilink.target[len("translation:") :]
    instance.en_page = page
    wikilink.string = ""
    return True


wikilink.register_namespace(":category", category_link_replace)
wikilink.register_namespace("category", category_replace)
wikilink.register_namespace(":folder", folder_link_replace)
wikilink.register_namespace(":template", template_replace)
wikilink.register_namespace("template", template_replace)
wikilink.register_namespace("translation", translation_replace)
