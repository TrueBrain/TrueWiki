import unicodedata
import urllib

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


DISALLOWED_NAMES = (
    "..",  # Path-walking.
    ":",  # Namespace indicator.
    "|",  # Just .. don't.
    "#",  # Makes hash-parts of URLs difficult.
    "[",  # wikitext syntax.
    "]",  # wikitext syntax.
    "{",  # wikitext syntax.
    "}",  # wikitext syntax.
    "_",  # Use a space instead.
    "<",  # Reserved character on NTFS.
    ">",  # Reserved character on NTFS.
    "\\",  # Reserved character on NTFS.
    '"',  # Reserved character on NTFS.
    "*",  # Reserved character on NTFS.
    "?",  # Reserved character on NTFS.
)

DISALLOWS_PARTS_LEADING = (
    " ",  # Most likely a mistake by the user.
    ".",  # Don't allow "hidden" files.
)
DISALLOWS_PARTS_TRAILING = (" ",)  # Most likely a mistake by the user.


def _check_illegal_names(user, new_page: str) -> Optional[str]:
    for disallowed_name in DISALLOWED_NAMES:
        if disallowed_name in new_page:
            return f'Page name "{new_page}" contains "{disallowed_name}", which is not allowed.'

    if new_page.endswith("/"):
        return (
            f'Page name "{new_page}" cannot end with a "/". If you want to create a main page for this folder, '
            'create a page called "Main Page" in this folder. '
            '"Main Page" cannot be translated, and is always written in English, no matter the language you are in.'
        )

    if new_page.startswith("/"):
        return f'Page name "{new_page}" starts with a "/", which is not allowed.'

    for part in new_page.split("/"):
        if not part:
            return f'Page name "{new_page}" contains a folder that is empty, which is not allowed.'

        if part.startswith(DISALLOWS_PARTS_LEADING):
            return (
                f'Page name "{new_page}" contains a filename/folder that starts with a space and/or dot, '
                "which is not allowed."
            )

        if part.endswith(DISALLOWS_PARTS_TRAILING):
            return f'Page name "{new_page}" contains a filename/folder that ends with a space, which is not allowed.'

    for letter in new_page:
        if unicodedata.category(letter)[0] == "C":
            return (
                f'Page name "{new_page}" contains '
                '<a href="https://en.wikipedia.org/wiki/Control_character" target="_new">Control Characters</a>, '
                "which is not allowed."
            )

    return None


def save(user, old_page: str, new_page: str, content: str, payload) -> web.Response:
    wiki_page = WikiPage(old_page)
    if not wiki_page.page_is_valid(old_page):
        return error.view(user, old_page, "Error 404 - File not found")
    if not wiki_page.page_is_valid(new_page):
        return error.view(
            user,
            new_page,
            f'Page name "{new_page}" is not a valid name; does it start with a language code?',
        )

    error_message = _check_illegal_names(user, new_page)
    if error_message is not None:
        return error.view(
            user,
            old_page,
            error_message,
            status=401,
        )

    # If the old page doesn't exist, this creates a page. But it is possible
    # that this is done from an old page with a different name. Make sure the
    # new page always wins in this case.
    if not wiki_page.page_exists(old_page):
        create_new = True
        old_page = new_page
        commit_message = f"new page: {old_page}"
    else:
        create_new = False
        commit_message = f"modified: {old_page}"

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

    # Check with the namespace callback if there is an error.
    namespace_error = wiki_page.edit_callback(old_page, new_page, payload)
    if namespace_error:
        return error.view(user, old_page, namespace_error)

    changed = []

    if old_page != new_page:
        commit_message = f"renamed: {old_page} -> {new_page}"

        # Inform the namespace of the change in name.
        wiki_page.edit_rename(old_page, new_page)

        # Remove the old file.
        singleton.STORAGE.file_remove(old_filename)
        changed.append(old_filename[: -len(".mediawiki")])

    new_filename = wiki_page.page_ondisk_name(new_page)
    new_dirname = "/".join(new_filename.split("/")[:-1])

    # Make sure the folder exists.
    singleton.STORAGE.dir_make(new_dirname)
    # Write the new source.
    singleton.STORAGE.file_write(new_filename, content.replace("\r", ""))

    # Inform the namespace of the edit.
    wiki_page.edit_callback(old_page, new_page, payload, execute=True)

    singleton.STORAGE.commit(user, commit_message)

    changed.append(new_filename[: -len(".mediawiki")])
    page_changed(changed)

    location = urllib.parse.quote(new_page)
    return web.HTTPFound(f"/{location}")


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

    body = source.create_body(wiki_page, user, "Edit", new_page=page)
    return web.Response(body=body, content_type="text/html")
