import glob
import os

from . import singleton
from .wiki_page import WikiPage


def validate_folder(folder, ignore_index):
    for item in sorted(glob.glob(f"{folder}/*")):
        if os.path.isdir(item):
            validate_folder(item, ignore_index)
            continue

        if not item.endswith(".mediawiki"):
            continue

        item = item[ignore_index : -len(".mediawiki")]
        if item.startswith("Page/"):
            item = item[len("Page/") :]

        try:
            wiki_page = WikiPage(item).render()
        except Exception as e:
            print(f"{item}:")
            print(" - EXCEPTION: ", e)
            continue

        if wiki_page.errors:
            print(f"{item}:")
            for error in wiki_page.errors:
                print(f" - {error}")


def all():
    validate_folder(singleton.STORAGE.folder, len(singleton.STORAGE.folder) + 1)
