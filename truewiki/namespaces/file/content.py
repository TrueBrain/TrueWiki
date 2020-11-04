import os
import wikitextparser

from wikitexthtml.render import wikilink

from ... import singleton
from ...wiki_page import WikiPage
from ...wrapper import wrap_page

FILESIZE_POSTFIX = [
    "bytes",
    "kB",
    "MB",
]


def add_content(page):
    wiki_page = WikiPage(page)

    filename = wiki_page.page_ondisk_name(page)
    filename = filename[:-len(".mediawiki")]

    caption = ""
    if filename:
        filesize = os.path.getsize(f"{singleton.STORAGE.folder}/{filename}")

        # Find a nice magnitude to present the filesize in.
        filesize_magnitude = 0
        while filesize > 512 and filesize_magnitude < len(FILESIZE_POSTFIX) - 1:
            filesize /= 1024
            filesize_magnitude += 1
        filesize = round(filesize, 2)

        # Add in the caption the filesize.
        caption = f'<div class="center">Filesize: {filesize} {FILESIZE_POSTFIX[filesize_magnitude]}</div>'

    # Generate the image via a wikilink.
    body = f"[[File:{page[len('File/'):]}|center|link=|frame|{caption}]]"

    # Find the history page of the image itself.
    history_url = singleton.STORAGE.get_history_url(filename)
    if history_url:
        body += f'<h2>File history</h2><a href="{history_url}">Click here to view the history of the file itself</a>.'

    wtp = wikitextparser.parse(body)
    wikilink.replace(wiki_page, wtp)
    templates = {"content": wtp.string}

    return wrap_page(page, "File", {}, templates)
