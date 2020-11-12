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

RELOAD_BUSY = asyncio.Event()
RELOAD_BUSY.set()

METADATA_READY = asyncio.Event()


def translation_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Translation:"):
            target = wikilink.target[len("Translation:") :].strip()
            PAGES[page]["translations"].append(target)
            TRANSLATIONS[target].append(page)


def category_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Category:"):
            target = wikilink.target[len("Category:") :].strip()
            PAGES[page]["categories"].append(target)
            CATEGORIES[target].append(page)


def file_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("File:"):
            target = wikilink.target[len("File:") :].strip()
            PAGES[page]["files"].append(target)
            FILES[target].append(page)


def links_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if ":" not in wikilink.target or wikilink.target.startswith(":"):
            if ":" not in wikilink.target:
                target = f":Page:{wikilink.target}"
            else:
                target = wikilink.target
            target = target.strip()

            PAGES[page]["links"].append(target)
            LINKS[target].append(page)


def template_callback(wtp, wiki_page, page):
    for template in wiki_page.templates:
        if ":" in template:
            namespace, _, template = template.partition(":")
        else:
            namespace = "Template"

        target = f"{namespace}/{template}".strip()
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
    for file in PAGES[page]["files"]:
        FILES[file].remove(page)
    for link in PAGES[page]["links"]:
        LINKS[link].remove(page)
    for template in PAGES[page]["templates"]:
        TEMPLATES[template].remove(page)
    for translation in PAGES[page]["translations"]:
        TRANSLATIONS[translation].remove(page)

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


def _page_changed(page, notified=None):
    if notified is None:
        notified = set()

    if page in notified:
        return

    # Capture the current templates ued. After analysis, this might have
    # changed, but those are still pages that need to be analyzed again.
    dependencies = TEMPLATES[page].copy()

    notified.add(page)
    _analyze_page(page)

    # Notify all dependencies of a page change.
    for dependency in TEMPLATES[page] + dependencies:
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


def load_metadata():
    METADATA_READY.clear()

    loop = asyncio.get_event_loop()
    loop.create_task(out_of_process("load_metadata", None))


def page_changed(pages):
    loop = asyncio.get_event_loop()
    loop.create_task(out_of_process("page_changed", pages))


async def out_of_process(func, pages):
    global CATEGORIES, FILES, LANGUAGES, LINKS, PAGES, PAGES_LC, TEMPLATES, TRANSLATIONS

    await RELOAD_BUSY.wait()
    RELOAD_BUSY.clear()

    try:
        reload_helper = ReloadHelper(pages)

        # Run the reload in a new process, so we don't block the rest of the
        # server while doing this job.
        loop = asyncio.get_event_loop()
        with futures.ProcessPoolExecutor(max_workers=1) as executor:
            task = loop.run_in_executor(executor, getattr(reload_helper, func))
            (
                CATEGORIES,
                FILES,
                LANGUAGES,
                LINKS,
                PAGES,
                PAGES_LC,
                TEMPLATES,
                TRANSLATIONS,
            ) = await task
    finally:
        RELOAD_BUSY.set()

    if func == "load_metadata":
        METADATA_READY.set()


class ReloadHelper:
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

        # Ensure thare are no duplicated in PAGES too, and fill the PAGES_LC
        # with a mapping from lowercase to real page name.
        PAGES_LC.clear()
        for page, page_data in PAGES.items():
            page_data["categories"] = list(set(page_data["categories"]))
            page_data["files"] = list(set(page_data["files"]))
            page_data["links"] = list(set(page_data["links"]))
            page_data["templates"] = list(set(page_data["templates"]))
            page_data["translations"] = list(set(page_data["translations"]))

            PAGES_LC[page.lower()] = page

    def page_changed(self):
        for page in self.pages:
            _page_changed(page)
        self._post()

        return CATEGORIES, FILES, LANGUAGES, LINKS, PAGES, PAGES_LC, TEMPLATES, TRANSLATIONS

    def _load_metadata_from_cache(self):
        with open(CACHE_FILENAME, "r") as fp:
            try:
                payload = json.loads(fp.read())
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

    def load_metadata(self):
        start = time.time()
        log.info("Loading metadata (this can take a while the first run) ...")

        CATEGORIES.clear()
        FILES.clear()
        LANGUAGES.clear()
        LINKS.clear()
        PAGES.clear()
        TEMPLATES.clear()
        TRANSLATIONS.clear()

        if os.path.exists(CACHE_FILENAME):
            self._load_metadata_from_cache()

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
            pages_seen.update(_scan_folder(f"{subfolder}", notified))

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
        return CATEGORIES, FILES, LANGUAGES, LINKS, PAGES, PAGES_LC, TEMPLATES, TRANSLATIONS


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
