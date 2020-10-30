import glob
import os

from collections import defaultdict

TRANSLATIONS = defaultdict(list)
CATEGORIES = defaultdict(list)
DEPENDENCIES = defaultdict(list)


def scan_folder(folder, ignore_index, callbacks):
    # Delay the import of WikiPage, as WikiPage needs this module too.
    from .wiki_page import WikiPage

    for node in glob.glob(f"{folder}/*"):
        if os.path.isdir(node):
            scan_folder(node, ignore_index, callbacks)
            continue

        if node.endswith(".mediawiki"):
            page = node[ignore_index : -len(".mediawiki")]

            with open(node, "r") as fp:
                body = fp.read()
            wiki_page = WikiPage(page)
            wtp = wiki_page.prepare(body)

            for callback in callbacks:
                callback(wtp, wiki_page, page)


def translation_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Translation:"):
            target = wikilink.target[len("Translation:") :]
            TRANSLATIONS[target].append(page)


def category_callback(wtp, wiki_page, page):
    for wikilink in wtp.wikilinks:
        if wikilink.target.startswith("Category:"):
            target = wikilink.target[len("Category:") :]
            CATEGORIES[target].append(page)


def dependency_callback(wtp, wiki_page, page):
    for template in wiki_page.templates:
        target = f"Template/{template}"
        DEPENDENCIES[target].append(page)


def load_metadata(folder):
    TRANSLATIONS.clear()
    CATEGORIES.clear()
    DEPENDENCIES.clear()

    callbacks = [
        category_callback,
        dependency_callback,
        translation_callback,
    ]

    for subfolder in ("Page", "Template", "Category"):
        scan_folder(f"{folder}/{subfolder}", len(f"{folder}/"), callbacks)

    for translation in TRANSLATIONS:
        TRANSLATIONS[translation] = sorted(TRANSLATIONS[translation], key=lambda name: (name.find("en/") < 0, name))

    for category in CATEGORIES:
        CATEGORIES[category] = sorted(CATEGORIES[category])
