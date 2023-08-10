import aiohttp
import click
import hashlib
import os
import time

from aiohttp import web
from openttd_helpers import click_helper

from . import error
from .. import metadata
from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page

CACHE_PAGE_FOLDER = None


def _view(wiki_page, user, page: str) -> web.Response:
    templates = {
        "content": wiki_page.render().html,
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
        "errors": len(wiki_page.errors) if wiki_page.errors else "",
    }

    templates["language"] = wiki_page.add_language(page)
    templates["footer"] = wiki_page.add_footer(page)
    templates["content"] += wiki_page.add_content(page)

    return wrap_page(page, "Page", variables, templates)


def view(user, page: str, if_modified_since, if_none_match) -> web.Response:
    if page.endswith("/"):
        page += "Main Page"

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
            f'"{page}" does not exist; did you mean [[{correct_page}]]?',
        )

    status_code = 200 if wiki_page.page_exists(page) else 404
    namespaced_page = page
    if not namespaced_page.startswith(("Category/", "File/", "Folder/", "Template/")):
        namespaced_page = f"Page/{namespaced_page}"

    can_cache = status_code == 200 and not namespaced_page.startswith("Folder/")

    if CACHE_PAGE_FOLDER:
        cache_filename = f"{CACHE_PAGE_FOLDER}/{namespaced_page}.html"
    else:
        cache_filename = None

    response = None

    # Check as we might have this page already on cache.
    if can_cache and namespaced_page in metadata.LAST_TIME_RENDERED:
        if (
            if_modified_since is not None
            and metadata.LAST_TIME_RENDERED[namespaced_page][0] <= if_modified_since.timestamp()
        ):
            # We already rendered this page before. If the browser has it in his
            # cache, he can simply reuse that if we haven't rendered since.
            response = web.HTTPNotModified()
        elif (
            not user and if_none_match is not None and metadata.LAST_TIME_RENDERED[namespaced_page][1] == if_none_match
        ):
            # We already rendered this page before. If the browser has it in his
            # cache, he can simply reuse that if the content is still the same.
            response = web.HTTPNotModified()
        elif (
            not user
            and cache_filename
            and os.path.exists(cache_filename)
            and os.path.getmtime(cache_filename) >= metadata.LAST_TIME_RENDERED[namespaced_page][0]
        ):
            # We already rendered this page to disk. Serve from there.
            with open(cache_filename) as fp:
                body = fp.read()
            response = web.Response(body=body, content_type="text/html", status=status_code)

    # Cache miss; render the page.
    if response is None:
        body = _view(wiki_page, user, page)

        # Never cache anything in the Folder/.
        if can_cache:
            if not user and cache_filename:
                # Cache the file on disk
                os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
                with open(cache_filename, "w") as fp:
                    fp.write(body)

                page_time = os.path.getmtime(cache_filename)
            else:
                # Accuracy of time.time() is higher than getmtime(), so
                # depending if we cached, use a different clock.
                page_time = time.time()

            # Only update the time if we don't have one yet. This makes sure
            # that LAST_TIME_RENDERED has the oldest timestamp possible.
            if namespaced_page not in metadata.LAST_TIME_RENDERED:
                metadata.LAST_TIME_RENDERED[namespaced_page] = (page_time, None)

            # Update the ETag if we don't have one yet. We only generate ETags for anonymous users.
            if not user and metadata.LAST_TIME_RENDERED[namespaced_page][1] is None:
                etag = hashlib.sha256(body.encode("utf-8")).hexdigest()
                metadata.LAST_TIME_RENDERED[namespaced_page] = (metadata.LAST_TIME_RENDERED[namespaced_page][0], etag)

                if if_none_match is not None and etag == if_none_match:
                    # Now we rendered the page, we find out that the etag did match after all.
                    # Return this information to the client, instead of the payload.
                    response = web.HTTPNotModified()

        if response is None:
            response = web.Response(body=body, content_type="text/html", status=status_code)

    # Inform the browser under which rules it can cache this page.
    if can_cache:
        response.last_modified = metadata.LAST_TIME_RENDERED[namespaced_page][0]
        if not user:
            # ETags are weak, as we don't actually know if we are byte-for-byte the same because
            # of things like gzip compression.
            response.etag = aiohttp.ETag(metadata.LAST_TIME_RENDERED[namespaced_page][1], is_weak=True)
        response.headers["Vary"] = "Accept-Encoding, Cookie"
        response.headers["Cache-Control"] = "private, must-revalidate, max-age=0"
    return response


@click_helper.extend
@click.option(
    "--cache-page-folder",
    help="Folder used to cache rendered pages.",
    default=None,
    show_default=True,
)
def click_page(cache_page_folder):
    global CACHE_PAGE_FOLDER

    if cache_page_folder and cache_page_folder.endswith("/"):
        cache_page_folder = cache_page_folder[:-1]
    if not cache_page_folder:
        cache_page_folder = None

    CACHE_PAGE_FOLDER = cache_page_folder
