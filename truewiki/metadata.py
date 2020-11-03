import asyncio
import click
import glob
import hashlib
import json
import logging
import os
import time

from collections import defaultdict
from concurrent import futures
from openttd_helpers import click_helper

from . import singleton
from .wiki_page import WikiPage

log = logging.getLogger(__name__)

CACHE_FILENAME = ".cache_metadata.json"


def page():
    return {
        "translations": [],
        "categories": [],
        "dependencies": set(),
        "dependent_on": [],
        "digest": "",
    }


TRANSLATIONS = defaultdict(list)
CATEGORIES = defaultdict(list)
PAGES = defaultdict(page)

RELOAD_BUSY = asyncio.Event()
RELOAD_BUSY.set()


def translation_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Translation:"):
            target = wikilink.target[len("Translation:") :]
            PAGES[page]["translations"].append(target)
            TRANSLATIONS[target].append(page)


def category_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Category:"):
            target = wikilink.target[len("Category:") :]
            PAGES[page]["categories"].append(target)
            CATEGORIES[target].append(page)


def dependency_callback(wtp, wiki_page, page):
    for template in wiki_page.templates:
        target = f"Template/{template}"
        PAGES[page]["dependent_on"].append(target)
        PAGES[target]["dependencies"].add(page)


CALLBACKS = [
    category_callback,
    dependency_callback,
    translation_callback,
]


def _forget_page(page):
    for dependent_on in PAGES[page]["dependent_on"]:
        PAGES[dependent_on]["dependencies"].remove(page)
    for category in PAGES[page]["categories"]:
        CATEGORIES[category].remove(page)
    for translation in PAGES[page]["translations"]:
        TRANSLATIONS[translation].remove(page)

    PAGES[page]["dependent_on"].clear()
    PAGES[page]["categories"].clear()
    PAGES[page]["translations"].clear()


def _analyze_page(page):
    # Remove the page first from our existing index.
    if page in PAGES:
        _forget_page(page)

    # Analyze the file.
    with open(f"{singleton.STORAGE.folder}/{page}.mediawiki", "r") as fp:
        body = fp.read()

    wiki_page = WikiPage(page)
    wtp = wiki_page.prepare(body)

    # Index this page again.
    for callback in CALLBACKS:
        callback(wtp, wiki_page, page)


def _page_changed(page, notified=None):
    if notified is None:
        notified = set()

    if page in notified:
        return

    # Capture the current dependencies. After analysis, this might have
    # changed, but those are still pages that need to be analyzed again.
    dependencies = PAGES[page]["dependencies"].copy()

    notified.add(page)
    _analyze_page(page)

    # Notify all dependencies of a page change.
    for dependency in PAGES[page]["dependencies"] | dependencies:
        _page_changed(dependency, notified)


def _scan_folder(folder, notified=None):
    pages_seen = set()

    if notified is None:
        notified = set()

    for node in glob.glob(f"{singleton.STORAGE.folder}/{folder}/*"):
        if os.path.isdir(node):
            folder = node[len(singleton.STORAGE.folder) + 1 :]
            pages_seen.update(_scan_folder(folder, notified))
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

            _page_changed(page, notified)

    return pages_seen


def json_set_serialize(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


def load_metadata():
    loop = asyncio.get_event_loop()
    loop.create_task(out_of_process("load_metadata", None))


def page_changed(page):
    loop = asyncio.get_event_loop()
    loop.create_task(out_of_process("page_changed", page))


async def out_of_process(func, page):
    global TRANSLATIONS, CATEGORIES, PAGES

    await RELOAD_BUSY.wait()
    RELOAD_BUSY.clear()

    try:
        reload_helper = ReloadHelper(page)

        # Run the reload in a new process, so we don't block the rest of the
        # server while doing this job.
        loop = asyncio.get_event_loop()
        with futures.ProcessPoolExecutor(max_workers=1) as executor:
            task = loop.run_in_executor(executor, getattr(reload_helper, func))
            (
                TRANSLATIONS,
                CATEGORIES,
                PAGES,
            ) = await task
    finally:
        RELOAD_BUSY.set()


class ReloadHelper:
    def __init__(self, page):
        self.page = page

    def page_changed(self):
        _page_changed(self.page)

        return TRANSLATIONS, CATEGORIES, PAGES

    def load_metadata(self):
        start = time.time()
        log.info("Loading metadata (this can take a while the first run) ...")

        TRANSLATIONS.clear()
        CATEGORIES.clear()
        PAGES.clear()

        if os.path.exists(CACHE_FILENAME):
            with open(CACHE_FILENAME, "r") as fp:
                payload = json.loads(fp.read())
                TRANSLATIONS.update(payload["translations"])
                CATEGORIES.update(payload["categories"])
                PAGES.update(payload["pages"])

            # After JSON dumps/loads, set became lists; make sure all sets are sets again.
            for page in PAGES:
                PAGES[page]["dependencies"] = set(PAGES[page]["dependencies"])

        # Ensure no file is scanned more than once.
        notified = set()
        # Keep track of which pages we have seen.
        pages_seen = set()
        # Scan all folders with mediawiki files.
        for subfolder in ("Page", "Template", "Category"):
            pages_seen.update(_scan_folder(f"{subfolder}", notified))

        # If we come from cache, validate that no file got removed; we should
        # forget about those.
        pages_known = set(page for page in PAGES if PAGES[page]["digest"])
        for page in pages_seen:
            if page in pages_known:
                pages_known.remove(page)
        for page in pages_known:
            _forget_page(page)

        # Sort all translations and categories; makes it easier for the render.
        for translation in TRANSLATIONS:
            TRANSLATIONS[translation] = sorted(TRANSLATIONS[translation], key=lambda name: (name.find("en/") < 0, name))
        for category in CATEGORIES:
            CATEGORIES[category] = sorted(CATEGORIES[category])

        with open(CACHE_FILENAME, "w") as fp:
            fp.write(
                json.dumps(
                    {
                        "translations": TRANSLATIONS,
                        "categories": CATEGORIES,
                        "pages": PAGES,
                    },
                    default=json_set_serialize,
                )
            )

        log.info(f"Loading metadata done; took {time.time() - start:.2f} seconds")
        return TRANSLATIONS, CATEGORIES, PAGES


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
