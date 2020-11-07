import os
import unicodedata

from aiohttp import web
from typing import Optional

from . import (
    error,
    source,
)
from .. import (
    metadata,
    singleton,
)
from ..metadata import page_changed
from ..wiki_page import WikiPage


def _check_illegal_names(user, page: str, new_page: str) -> Optional[web.Response]:
    if ".." in new_page or new_page.strip(" .") != new_page:
        return error.view(
            user,
            page,
            f'Page name "{new_page}" contain ".." and/or starts/ends with a space and/or dot, which is not allowed.',
            status=401,
        )

    if new_page.endswith("/"):
        return error.view(
            user,
            page,
            f'Page name "{new_page}" cannot end with a "/". If you want to create a main page for this folder, '
            'create a page called "Main Page" in this folder. '
            '"Main Page" cannot be translated, and is always written in English, no matter the language you are in.',
            status=401,
        )

    for letter in new_page:
        if unicodedata.category(letter)[0] == "C":
            return error.view(
                user,
                page,
                f'Page name "{new_page}" contains '
                '<a href="https://en.wikipedia.org/wiki/Control_character" target="_new">Control Characters</a>, '
                "which is not allowed.",
                status=401,
            )

    return None


def save(user, old_page: str, new_page: str, content: str) -> web.Response:
    wiki_page = WikiPage(old_page)
    if not wiki_page.page_is_valid(old_page):
        return error.view(user, old_page, "Error 404 - File not found")
    if not wiki_page.page_is_valid(new_page):
        return error.view(
            user,
            new_page,
            f'Page name "{new_page}" is not a valid name; does it start with a language code?',
        )

    response = _check_illegal_names(user, old_page, new_page)
    if response is not None:
        return response

    # If the old page doesn't exist, this creates a page. But it is possible
    # that this is done from an old page with a different name. Make sure the
    # new page always wins in this case.
    if not wiki_page.page_exists(old_page):
        create_new = True
        old_page = new_page
    else:
        create_new = False

    old_filename = wiki_page.page_ondisk_name(old_page)

    # If we are not renaming to the same page (in lower-case), ensure we are
    # not renaming to a page similar but with different casing.
    if old_page.lower() != new_page.lower() or create_new:
        if wiki_page.page_exists(new_page):
            return error.view(
                user,
                old_page,
                f'Page name "{new_page}" already exists.',
            )

        correct_page = wiki_page.page_get_correct_case(new_page)
        if correct_page != new_page:
            return error.view(
                user,
                old_page,
                f'Page name "{new_page}" conflicts with "{correct_page}", which already exists.',
            )

        # Validate that if the page exists, we are not renaming it while there are
        # other pages depending on us
        if wiki_page.page_exists(old_page) and metadata.TEMPLATES[old_filename[: -len(".mediawiki")]]:
            return error.view(user, old_page, "Cannot rename page as other pages depend on it.")

    changed = []

    if old_page != new_page:
        # Remove the old file.
        os.unlink(f"{singleton.STORAGE.folder}/{old_filename}")
        changed.append(old_filename[: -len(".mediawiki")])

    new_filename = wiki_page.page_ondisk_name(new_page)
    new_dirname = "/".join(new_filename.split("/")[:-1])

    # Make sure the folder exists.
    os.makedirs(f"{singleton.STORAGE.folder}/{new_dirname}", exist_ok=True)
    # Write the new source.
    with open(f"{singleton.STORAGE.folder}/{new_filename}", "w") as fp:
        fp.write(content)

    changed.append(new_filename[: -len(".mediawiki")])
    page_changed(changed)

    return web.HTTPFound(f"/{new_page}")


def view(user, page: str) -> web.Response:
    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return error.view(user, page, "Error 404 - File not found")

    # If there is a difference in case, nicely point this out to users.
    correct_page = wiki_page.page_get_correct_case(page)
    if correct_page != page:
        return error.view(
            user,
            page,
            f'Page name "{page}" conflicts with "{correct_page}". Did you mean to edit [[{correct_page}]]?',
        )

    body = source.create_body(wiki_page, user, "Edit")
    return web.Response(body=body, content_type="text/html")
