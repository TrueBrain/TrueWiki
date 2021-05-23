import os
import urllib.parse

from aiohttp import web

from . import page as page_view
from .. import (
    singleton,
    metadata,
)


def view() -> web.Response:
    if singleton.FRONTEND_URL is None:
        raise web.HTTPNotFound

    if page_view.CACHE_PAGE_FOLDER:
        cache_filename = f"{page_view.CACHE_PAGE_FOLDER}/sitemap.xml"
    else:
        cache_filename = None

    # Check if we have this file in cache first.
    if cache_filename and os.path.exists(cache_filename):
        with open(cache_filename) as fp:
            body = fp.read()
    else:
        body = '<?xml version="1.0" encoding="UTF-8"?>\n'
        body += (
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        )

        for page, page_data in metadata.PAGES.items():
            if page.startswith("Page/"):
                page = page[len("Page/") :]
            page = urllib.parse.quote(page)

            body += "<url>\n"
            body += f"<loc>{singleton.FRONTEND_URL}/{page}</loc>\n"

            if len(page_data["translations"]) == 1:
                en_page = page_data["translations"][0]

                if len(metadata.TRANSLATIONS[en_page]) > 1:
                    for translation in metadata.TRANSLATIONS[en_page]:
                        if translation.startswith("Page/"):
                            language = translation.split("/")[1]
                            translation = translation[len("Page/") :]
                        else:
                            language = translation.split("/")[1]
                        if translation.endswith("/Main Page"):
                            translation = translation[: -len("/Main Page")] + "/"

                        translation = urllib.parse.quote(translation)
                        body += (
                            f'<xhtml:link rel="alternate" hreflang="{language}" '
                            f'href="{singleton.FRONTEND_URL}/{translation}" />\n'
                        )

            body += "</url>\n"

        body += "</urlset>\n"

        if cache_filename:
            # Store in cache for next time it is requested.
            os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
            with open(cache_filename, "w") as fp:
                fp.write(body)

    return web.Response(body=body, content_type="application/xml")


def invalidate_cache() -> None:
    if not page_view.CACHE_PAGE_FOLDER:
        return

    cache_filename = f"{page_view.CACHE_PAGE_FOLDER}/sitemap.xml"

    if os.path.exists(cache_filename):
        os.unlink(cache_filename)
