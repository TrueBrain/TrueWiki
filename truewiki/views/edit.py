import urllib

from aiohttp import web

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


def save(user, old_page: str, new_page: str, content: str, payload, summary: str = None) -> web.Response:
    wiki_page = WikiPage(old_page)
    page_error = wiki_page.page_is_valid(old_page, is_new_page=True)
    if page_error:
        return error.view(user, old_page, page_error)

    if new_page.endswith("/"):
        page_error = (
            f'Page name "{new_page}" cannot end with a "/". If you meant the main page, please add "Main Page". '
            'The name of the page "Main Page" cannot be translated, and is always written in English, '
            "no matter the language you are in. The content of course can be translated."
        )
    else:
        page_error = wiki_page.page_is_valid(new_page, is_new_page=True)

    if page_error:
        body = source.create_body(wiki_page, user, "Edit", new_page=new_page, page_error=page_error)
        return web.Response(body=body, content_type="text/html")

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

    if summary:
        commit_message += f"\n User Summary: {summary}"

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
    singleton.STORAGE.file_write(new_filename, content)

    # Inform the namespace of the edit.
    wiki_page.edit_callback(old_page, new_page, payload, execute=True)

    singleton.STORAGE.commit(user, commit_message)

    changed.append(new_filename[: -len(".mediawiki")])
    page_changed(changed)

    location = urllib.parse.quote(new_page)
    return web.HTTPFound(f"/{location}")


def view(user, page: str) -> web.Response:
    wiki_page = WikiPage(page)
    page_error = wiki_page.page_is_valid(page)
    if page_error:
        return error.view(user, page, page_error)

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
