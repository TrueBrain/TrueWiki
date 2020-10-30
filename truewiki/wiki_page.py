import logging
import os

from typing import Optional
from wikitexthtml import Page

from . import (
    metadata,
    singleton,
)

log = logging.getLogger(__name__)

SPECIAL_FOLDERS = (
    "Category/",
    "Folder/",
    "Template/",
)


class WikiPage(Page):
    def __init__(self, page: str) -> None:
        super().__init__(page)
        self.en_page = None
        self.categories = []
        self._folder = singleton.STORAGE.folder

    def page_load(self, page: str) -> str:
        for special_folder in SPECIAL_FOLDERS:
            if page.startswith(special_folder):
                prefix = special_folder[:-1]
                page = page[len(special_folder) :]
                break
        else:
            prefix = "Page"

        filename = f"{self._folder}/{prefix}/{page}.mediawiki"

        if not os.path.exists(filename):
            return ""

        with open(filename) as fp:
            body = fp.read()
        return body

    def page_exists(self, page: str) -> bool:
        for special_folder in SPECIAL_FOLDERS:
            if page.startswith(special_folder):
                prefix = special_folder[:-1]
                page = page[len(special_folder) :]
                break
        else:
            prefix = "Page"

        if prefix == "Folder":
            # This is /Folder/, which should list all languages.
            if page == "Main Page":
                return True

            # /Folder only works with folders, which are extended with
            # "Main Page" automatically. So remove "Main Page", and check if
            # the folder exists on disk.
            if not page.endswith("/Main Page"):
                return False
            page = page[: -len("/Main Page")]
            return os.path.exists(f"{self._folder}/{page}")

        if prefix == "Category":
            # This is /Category/, which should list all languages.
            if page == "Main Page":
                return True
            # This is the root of the category of a language; here we list all
            # categories.
            if page.endswith("/Main Page") and len(page.split("/")) == 2:
                return True

            # A category might not have a mediawiki page, but has pages
            # in it.
            if page in metadata.CATEGORIES:
                return True
            # Fallthrough; a category might not have anything in it, but
            # still have a mediawiki page ready for it.

        if prefix == "Template":
            # This is /Template/, which should list all languages.
            if page == "Main Page":
                return True
            # Fallthrough; otherwise render a template like a page.

        return os.path.exists(f"{self._folder}/{prefix}/{page}.mediawiki")

    def page_ondisk_name(self, page: str) -> str:
        for special_folder in SPECIAL_FOLDERS:
            if page.startswith(special_folder):
                return f"{page}.mediawiki"
        if page.startswith("File/"):
            return f"{page}.mediawiki"
        return f"Page/{page}.mediawiki"

    def template_load(self, template: str) -> str:
        with open(f"{self._folder}/Template/{template}.mediawiki") as fp:
            return fp.read()

    def template_exists(self, template: str) -> bool:
        return os.path.exists(f"{self._folder}/Template/{template}.mediawiki")

    def file_exists(self, file: str) -> bool:
        return os.path.exists(f"{self._folder}/File/{file}")

    def clean_url(self, url: str) -> str:
        if url.endswith("Main Page"):
            return url[: -len("Main Page")]
        return url

    def clean_title(self, title: str) -> str:
        stitle = title.split("/")
        if stitle[-1] == "Main Page":
            if len(stitle) > 2:
                return stitle[-2]
            if stitle[0] + "/" in SPECIAL_FOLDERS:
                return stitle[0]
            return "OpenTTD's Wiki"

        return stitle[-1]

    def file_get_link(self, url: str) -> str:
        return f"/File/{url}"

    def file_get_img(self, url: str, thumb: Optional[int]) -> str:
        # TODO -- Support thumb sizes
        return f"/uploads/{url}"
