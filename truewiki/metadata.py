import asyncio
import click
import glob
import hashlib
import json
import logging
import os
import sys
import time

from collections import defaultdict
from openttd_helpers import click_helper

from . import (
    config,
    singleton,
)
from .wiki_page import WikiPage

log = logging.getLogger(__name__)

CACHE_FILENAME = ".cache_metadata.json"
CACHE_VERSION = 4


def page():
    return {
        "categories": [],
        "files": [],
        "links": [],
        "templates": [],
        "translations": [],
        "digest": "",
    }


CATEGORIES = defaultdict(list)
FILES = defaultdict(list)
LANGUAGES = set()
LINKS = defaultdict(list)
PAGES = defaultdict(page)
PAGES_LC = {}
TEMPLATES = defaultdict(list)
TRANSLATIONS = defaultdict(list)
LAST_TIME_RENDERED = {}

RELOAD_BUSY = asyncio.Event()
RELOAD_BUSY.set()


def _delete_cached_page(page):
    if page in LAST_TIME_RENDERED:
        del LAST_TIME_RENDERED[page]


def translation_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Translation:"):
            target = wikilink.target[len("Translation:") :].strip()
            target = sys.intern(target)
            PAGES[page]["translations"].append(target)
            TRANSLATIONS[target].append(page)

            # Reset the last time rendered for all translations too, as
            # otherwise a new translation won't show up on those pages.
            for translation in TRANSLATIONS[target]:
                _delete_cached_page(translation)


def category_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Category:"):
            target = wikilink.target[len("Category:") :].strip()
            target = sys.intern(target)
            PAGES[page]["categories"].append(target)
            CATEGORIES[target].append(page)

            # Reset the last time rendered for the category.
            _delete_cached_page(f"Category/{target}")


def file_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("File:"):
            target = wikilink.target[len("File:") :].strip()
            target = sys.intern(target)
            PAGES[page]["files"].append(target)
            FILES[target].append(page)

            # Reset the last time rendered for the file.
            _delete_cached_page(f"File/{target}")


def links_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if ":" not in wikilink.target or wikilink.target.startswith(":"):
            if ":" not in wikilink.target:
                target = f":Page:{wikilink.target}"
            else:
                target = wikilink.target
            target = target.strip()
            target = sys.intern(target)

            PAGES[page]["links"].append(target)
            LINKS[target].append(page)


def template_callback(wtp, wiki_page, page):
    for template in wiki_page.templates:
        if ":" in template:
            namespace, _, template = template.partition(":")
        else:
            namespace = "Template"

        target = f"{namespace}/{template}".strip()
        target = sys.intern(target)
        PAGES[page]["templates"].append(target)
        TEMPLATES[target].append(page)


CALLBACKS = [
    category_callback,
    file_callback,
    links_callback,
    template_callback,
    translation_callback,
]


def _forget_page(page):
    for category in PAGES[page]["categories"]:
        CATEGORIES[category].remove(page)
        _delete_cached_page(f"Category/{category}")
    for file in PAGES[page]["files"]:
        FILES[file].remove(page)
        _delete_cached_page(f"File/{file}")
    for link in PAGES[page]["links"]:
        LINKS[link].remove(page)
    for template in PAGES[page]["templates"]:
        TEMPLATES[template].remove(page)
    for translation in PAGES[page]["translations"]:
        TRANSLATIONS[translation].remove(page)

        # Reset the last time rendered for all translations too, as
        # otherwise a removed translation will still show up on those pages.
        if not translation.startswith(("Category/", "File/", "Template/")):
            translation = f"Page/{translation}"
        _delete_cached_page(translation)

    PAGES[page]["categories"].clear()
    PAGES[page]["files"].clear()
    PAGES[page]["links"].clear()
    PAGES[page]["templates"].clear()
    PAGES[page]["translations"].clear()


def _analyze_page(page):
    # Remove the page first from our existing index.
    if page in PAGES:
        _forget_page(page)

    # This file is removed since our last scan; forget about it.
    if not os.path.exists(f"{singleton.STORAGE.folder}/{page}.mediawiki"):
        # If the file is gone, remove it from our index completely.
        if page in PAGES:
            del PAGES[page]
        return

    # Analyze the file.
    with open(f"{singleton.STORAGE.folder}/{page}.mediawiki", "r") as fp:
        body = fp.read()

    if page.startswith("Page/"):
        page_name = page[len("Page/") :]
    else:
        page_name = page
    wiki_page = WikiPage(page_name)
    wtp = wiki_page.prepare(body)

    # Index this page again.
    for callback in CALLBACKS:
        callback(wtp, wiki_page, page)


async def _page_changed(page, notified=None):
    page = sys.intern(page)

    # Allow other tasks to do something now. This fraction is sufficient
    # to still return pages (while indexing), although with an increased
    # latency.
    await asyncio.sleep(0)

    if notified is None:
        notified = set()

    if page in notified:
        return

    # As we are invalidating this page, also reset when we last rendered it.
    # This means that on a next request for this page, browsers will be
    # given a new version too.
    _delete_cached_page(page)

    # Capture the current templates ued. After analysis, this might have
    # changed, but those are still pages that need to be analyzed again.
    dependencies = TEMPLATES[page].copy()

    notified.add(page)
    _analyze_page(page)

    # Notify all dependencies of a page change.
    for dependency in TEMPLATES[page] + dependencies:
        await _page_changed(dependency, notified)


async def _scan_folder(folder, notified=None):
    pages_seen = set()

    if notified is None:
        notified = set()

    for node in glob.glob(f"{singleton.STORAGE.folder}/{folder}/*"):
        if os.path.isdir(node):
            folder = node[len(singleton.STORAGE.folder) + 1 :]
            pages_seen.update(await _scan_folder(folder, notified))
            continue

        if node.endswith(".mediawiki"):
            page = node[len(singleton.STORAGE.folder) + 1 : -len(".mediawiki")]
            pages_seen.add(page)

            hash = hashlib.sha256()
            with open(node, "rb") as fp:
                hash.update(fp.read())
            digest = hash.hexdigest()

            # Use the hash of the file to see if this file is changed; if not,
            # we can safely skip analyzing it again. If any template used in
            # this page is changed, that template will trigger the correct
            # chain of updates.
            if PAGES[page]["digest"] == digest:
                continue
            PAGES[page]["digest"] = digest

            await _page_changed(page, notified)

    return pages_seen


def check_for_exception(task):
    exception = task.exception()
    if exception:
        log.exception("Exception in metadata_queue()", exc_info=exception)

        # We terminate the application, as this is a real problem from which we
        # cannot recover cleanly. This is needed, as we run in a co-routine, and
        # there is no other way to notify the main thread we are terminating.
        sys.exit(1)


def load_metadata():
    loop = asyncio.get_event_loop()
    task = loop.create_task(metadata_queue("load_metadata", None))
    task.add_done_callback(check_for_exception)


def page_changed(pages):
    loop = asyncio.get_event_loop()
    loop.create_task(metadata_queue("page_changed", pages))


async def metadata_queue(func, pages):
    await RELOAD_BUSY.wait()
    RELOAD_BUSY.clear()

    try:
        instance = MetadataQueue(pages)
        instance_func = getattr(instance, func)
        await instance_func()
    finally:
        RELOAD_BUSY.set()


def object_pairs_hook(items):
    """
    Use sys.intern() over every possible string we can sniff out.

    We do this, as we reuse the same string a lot, and this heavily reduces
    memory usage.
    """
    result = {}
    for key, value in items:
        key = sys.intern(key)

        if isinstance(value, dict):
            result[key] = object_pairs_hook(value.items())
        elif isinstance(value, list):
            result[key] = [sys.intern(v) for v in value]
        elif isinstance(value, str):
            result[key] = sys.intern(value)
        elif isinstance(value, int):
            result[key] = value
        else:
            raise NotImplementedError(f"Unknown type in json.loads() for {value}")

        # Validate we didn't change something
        assert result[key] == value

    return result


class MetadataQueue:
    def __init__(self, pages):
        self.pages = pages

    def _post(self):
        # Sort everything so we don't have to on render time.
        for category in CATEGORIES:
            CATEGORIES[category] = sorted(set(CATEGORIES[category]), key=lambda x: list(reversed(x.split("/"))))
        for file in FILES:
            FILES[file] = sorted(set(FILES[file]), key=lambda x: list(reversed(x.split("/"))))
        for link in LINKS:
            LINKS[link] = sorted(set(LINKS[link]), key=lambda x: list(reversed(x.split("/"))))
        for template in TEMPLATES:
            TEMPLATES[template] = sorted(set(TEMPLATES[template]), key=lambda x: list(reversed(x.split("/"))))
        for translation in TRANSLATIONS:
            TRANSLATIONS[translation] = sorted(
                set(TRANSLATIONS[translation]), key=lambda name: (name.find("en/") < 0, name)
            )

        # Ensure there are no duplicated in PAGES too, and fill the PAGES_LC
        # with a mapping from lowercase to real page name.
        PAGES_LC.clear()
        for page, page_data in PAGES.items():
            page_data["categories"] = list(set(page_data["categories"]))
            page_data["files"] = list(set(page_data["files"]))
            page_data["links"] = list(set(page_data["links"]))
            page_data["templates"] = list(set(page_data["templates"]))
            page_data["translations"] = list(set(page_data["translations"]))

            PAGES_LC[page.lower()] = page

    async def page_changed(self):
        for page in self.pages:
            await _page_changed(page)
        self._post()

    def _load_metadata_from_cache(self):
        with open(CACHE_FILENAME, "r") as fp:
            try:
                payload = json.loads(fp.read(), object_pairs_hook=object_pairs_hook)
            except json.JSONDecodeError:
                log.info("Cache was corrupted; reloading metadata ...")
                return

        if payload.get("version", 1) != CACHE_VERSION:
            return

        CATEGORIES.update(payload["categories"])
        FILES.update(payload["files"])
        LINKS.update(payload["links"])
        PAGES.update(payload["pages"])
        TEMPLATES.update(payload["templates"])
        TRANSLATIONS.update(payload["translations"])

    async def load_metadata(self):
        start = time.time()
        log.info("Loading metadata (this can take a while the first run) ...")

        CATEGORIES.clear()
        FILES.clear()
        LANGUAGES.clear()
        LINKS.clear()
        PAGES.clear()
        TEMPLATES.clear()
        TRANSLATIONS.clear()
        LAST_TIME_RENDERED.clear()

        if os.path.exists(CACHE_FILENAME):
            self._load_metadata_from_cache()

        # Ensure the primary language is always available.
        LANGUAGES.add(config.PRIMARY_LANGUAGE)

        # Ensure no file is scanned more than once.
        notified = set()
        # Keep track of which pages we have seen.
        pages_seen = set()
        # Scan all folders with mediawiki files.
        for subfolder in ("Page", "Template", "Category", "File"):
            # Index all languages (the superset of all folders).
            for node in glob.glob(f"{singleton.STORAGE.folder}/{subfolder}/*"):
                if os.path.isdir(node):
                    language = node.split("/")[-1]
                    LANGUAGES.add(language)
            pages_seen.update(await _scan_folder(f"{subfolder}", notified))

        # If we come from cache, validate that no file got removed; we should
        # forget about those.
        pages_known = set(page for page in PAGES if PAGES[page]["digest"])
        for page in pages_seen:
            if page in pages_known:
                pages_known.remove(page)
        for page in pages_known:
            _forget_page(page)
            del PAGES[page]

        self._post()

        with open(CACHE_FILENAME, "w") as fp:
            fp.write(
                json.dumps(
                    {
                        "version": CACHE_VERSION,
                        "categories": CATEGORIES,
                        "files": FILES,
                        "links": LINKS,
                        "pages": PAGES,
                        "templates": TEMPLATES,
                        "translations": TRANSLATIONS,
                    }
                )
            )

        log.info(f"Loading metadata done; took {time.time() - start:.2f} seconds")


@click_helper.extend
@click.option(
    "--cache-metadata-file",
    help="File used to cache metadata.",
    default=".cache_metadata.json",
    show_default=True,
)
def click_metadata(cache_metadata_file):
    global CACHE_FILENAME

    CACHE_FILENAME = cache_metadata_file
