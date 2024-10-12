import glob
import os

from . import singleton
from .wiki_page import WikiPage


def validate_folder(folder, ignore_index, errors):
    for item in sorted(glob.glob(f"{folder}/*")):
        if os.path.isdir(item):
            validate_folder(item, ignore_index, errors)
            continue

        if not item.endswith(".mediawiki"):
            continue

        item = item[ignore_index : -len(".mediawiki")]
        if item.startswith("Page/"):
            item = item[len("Page/") :]

        try:
            wiki_page = WikiPage(item).render()
        except Exception as e:
            if errors is None:
                print(f"{item}:")
                print(" - EXCEPTION: ", e)
            else:
                errors[item] = {"exception": str(e)}
            continue

        if wiki_page.errors:
            if errors is None:
                print(f"{item}:")
                for error in wiki_page.errors:
                    print(f" - {error}")
            else:
                errors[item] = {"errors": wiki_page.errors}


def all(errors):
    validate_folder(singleton.STORAGE.folder, len(singleton.STORAGE.folder) + 1, errors)
