import wikitextparser

from wikitexthtml.render import wikilink

from ... import singleton
from ...wiki_page import (
    NAMESPACE_MAPPING,
    WikiPage,
)
from ...wrapper import wrap_page

FILESIZE_POSTFIX = [
    "bytes",
    "KiB",
    "MiB",
]


def add_content(page):
    wiki_page = WikiPage(page)

    filename = wiki_page.page_ondisk_name(page)
    filename = filename[: -len(".mediawiki")]

    caption = ""
    if filename:
        filesize = singleton.STORAGE.file_getsize(filename)

        # Find a nice magnitude to present the filesize in.
        filesize_magnitude = 0
        while filesize > 512 and filesize_magnitude < len(FILESIZE_POSTFIX) - 1:
            filesize /= 1024
            filesize_magnitude += 1
        filesize = round(filesize, 2)

        # Add in the caption the filesize.
        caption = f'<div class="center">Filesize: {filesize} {FILESIZE_POSTFIX[filesize_magnitude]}</div>'

    used_on_pages = []
    if filename:
        for dependency in wiki_page.get_used_on_pages():
            namespace = NAMESPACE_MAPPING[dependency.split("/")[0] + "/"]
            dependency = "/".join(dependency.split("/")[1:])
            used_on_pages.append(f"<li>[[{namespace}{dependency}]]</li>")

    wtp = wikitextparser.parse("\n".join(used_on_pages))
    wikilink.replace(WikiPage(page), wtp)
    used_on_pages = wtp.string

    wtp = wikitextparser.parse(f"[[File:{page[len('File/'):]}|center|link=|frame|{caption}]]")
    wikilink.replace(wiki_page, wtp)
    content = wtp.string

    templates = {
        "content": content,
        "used_on_pages": used_on_pages,
    }

    variables = {
        "has_used_on_pages": "1" if used_on_pages else "",
        "file_history_url": singleton.STORAGE.get_history_url(filename),
    }

    return wrap_page(page, "snippet/File", variables, templates)
