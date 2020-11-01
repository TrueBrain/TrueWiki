import wikitextparser

from wikitexthtml.render import wikilink

from .. import metadata
from ..wiki_page import (
    NAMESPACE_MAPPING,
    WikiPage,
)


def create(instance: WikiPage, page: str):
    if not instance.en_page:
        return ""

    with open("templates/Language.mediawiki", "r") as fp:
        body = fp.read()

    language_content = ""
    for url in metadata.TRANSLATIONS.get(instance.en_page, []):
        if not url.startswith(tuple(NAMESPACE_MAPPING.keys())):
            raise RuntimeError(f"{url} has unknown namespace")

        language = url.split("/")[1]
        if url.startswith("Page/"):
            url = url[len("Page/") :]

        wtp = wikitextparser.parse(body)
        for template in reversed(wtp.templates):
            if template.name == "language":
                template.string = language
            elif template.name == "url":
                template.string = url

        wikilink.replace(WikiPage(page), wtp)
        language_content += wtp.string.strip()

    return language_content
