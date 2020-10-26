import glob
import os

from collections import defaultdict

from .wiki_page import WikiPage

TRANSLATIONS = defaultdict(list)
CATEGORIES = defaultdict(list)


def scan_folder(folder, ignore_index, callbacks):
    for node in glob.glob(f"{folder}/*"):
        if os.path.isdir(node):
            scan_folder(node, ignore_index, callbacks)
            continue

        if node.endswith(".mediawiki"):
            page = node[ignore_index : -len(".mediawiki")]

            with open(node, "r") as fp:
                body = fp.read()
            wtp = WikiPage(page).prepare(body)

            for callback in callbacks:
                callback(wtp, page)


def translation_callback(wtp, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Translation:"):
            TRANSLATIONS[wikilink.target[len("Translation:") :]].append(page)


def category_callback(wtp, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Category:"):
            CATEGORIES[wikilink.target[len("Category:") :]].append(page)


def load_metadata():
    scan_folder("data/Page", len("data/Page/"), [translation_callback, category_callback])
    scan_folder("data/Template", len("data/"), [translation_callback, category_callback])
    scan_folder("data/Category", len("data/"), [translation_callback, category_callback])

    for translation in TRANSLATIONS:
        TRANSLATIONS[translation] = sorted(TRANSLATIONS[translation], key=lambda name: (name.find("en/") < 0, name))

    for category in CATEGORIES:
        CATEGORIES[category] = sorted(CATEGORIES[category])
