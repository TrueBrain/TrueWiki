import os
import unicodedata

from aiohttp import web

from . import (
    error,
    source,
)
from .. import singleton
from ..metadata import page_changed
from ..wiki_page import WikiPage


def _check_illegal_names(user, page: str, new_page: str) -> web.Response:
    if ".." in new_page or new_page.strip(" .") != new_page:
        return error.view(
            user,
            page,
            f"Page '{new_page}' contain '..' and/or starts/ends with a space and/or dot, which is not allowed.",
            status=401,
        )

    for letter in new_page:
        if unicodedata.category(letter)[0] == "C":
            return error.view(
                user,
                page,
                f'Page "{new_page}" contains '
                '<a href="https://en.wikipedia.org/wiki/Control_character" target="_new">Control Characters</a>, '
                "which is not allowed.",
                status=401,
            )

    return None


def rename(user, old_page: str, new_page: str) -> web.Response:
    if new_page == old_page:
        return web.HTTPFound(f"/{old_page}")

    response = _check_illegal_names(user, old_page, new_page)
    if response:
        return response

    wiki_page = WikiPage(old_page)
    if not wiki_page.page_exists(old_page):
        return error.view(user, old_page, "Error 404 - File not found")

    # If we are not renaming to the same page (in lower-case), ensure we are
    # not renaming to a page similar but with different casing.
    if old_page.lower() != new_page.lower():
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

    # Read the old file from disk.
    old_filename = wiki_page.page_ondisk_name(old_page)
    with open(f"{singleton.STORAGE.folder}/{old_filename}") as fp:
        body = fp.read()

    new_filename = wiki_page.page_ondisk_name(new_page)
    new_dirname = "/".join(new_filename.split("/")[:-1])

    # Remove the old file.
    os.unlink(f"{singleton.STORAGE.folder}/{old_filename}")

    # Make sure the folder exists.
    os.makedirs(f"{singleton.STORAGE.folder}/{new_dirname}", exist_ok=True)
    # Write the new source.
    with open(f"{singleton.STORAGE.folder}/{new_filename}", "w") as fp:
        fp.write(body)

    page_changed(
        [
            old_filename[: -len(".mediawiki")],
            new_filename[: -len(".mediawiki")],
        ]
    )

    return web.HTTPFound(f"/{new_page}")


def save(user, page: str, change: str) -> web.Response:
    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return error.view(user, page, "Error 404 - File not found")

    response = _check_illegal_names(user, page, page)
    if response:
        return response

    # If there is a difference in case, nicely point this out to users.
    correct_page = wiki_page.page_get_correct_case(page)
    if correct_page != page:
        return error.view(
            user,
            page,
            f'Page name "{page}" conflicts with "{correct_page}". Did you mean to edit [[{correct_page}]]?',
        )

    filename = wiki_page.page_ondisk_name(page)
    dirname = "/".join(filename.split("/")[:-1])

    # Make sure the folder exists.
    os.makedirs(f"{singleton.STORAGE.folder}/{dirname}", exist_ok=True)
    # Write the new source.
    with open(f"{singleton.STORAGE.folder}/{filename}", "w") as fp:
        fp.write(change)

    page_changed([filename[: -len(".mediawiki")]])

    return web.HTTPFound(f"/{page}")


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
