import logging

from typing import Optional

from . import content
from .. import base
from ... import (
    singleton,
    wiki_page,
)

log = logging.getLogger(__name__)


class Namespace(base.Namespace):
    namespace = "Folder"
    force_link = ":Folder:"

    @staticmethod
    def _is_root(page: str) -> bool:
        return page == "Folder/Main Page"

    @staticmethod
    def _is_namespace_root(page: str) -> bool:
        return page.endswith("/Main Page") and len(page.split("/")) == 3

    @classmethod
    def page_load(cls, page: str) -> str:
        assert page.startswith("Folder/")

        if cls._is_root(page):
            return "A list of all namespaces with files and folders."

        if cls._is_namespace_root(page):
            return "A list of all the languages within this namespace."

        return "All the pages and folders inside this folder."

    @classmethod
    def page_exists(cls, page: str) -> bool:
        assert page.startswith("Folder/")

        if cls._is_root(page):
            return True

        if not page.endswith("/Main Page"):
            return False

        page = page[len("Folder/") : -len("/Main Page")]
        return singleton.STORAGE.dir_exists(page)

    @classmethod
    def page_is_valid(cls, page: str, is_new_page: bool) -> Optional[str]:
        assert page.startswith("Folder/")

        if not page.endswith("/Main Page"):
            return "You cannot view files in the Folder namespace."

        spage = page.split("/")

        if is_new_page:
            return "You cannot create new files in the Folder namespace."

        if cls._is_root(page):
            return None
        if cls._is_namespace_root(page):
            if not singleton.STORAGE.dir_exists(spage[1]):
                return f'Page name "{page}" is in namespace "{spage[1]}" that does not exist.'
            return None

        # There should always be a namespace and language code in the path.
        if len(spage) < 4:
            return f'Page name "{page}" is missing a namespace and/or language code.'
        # The namespace and language should already exist.
        if not singleton.STORAGE.dir_exists(f"{spage[1]}/{spage[2]}"):
            return f'Page name "{page}" is in language "{spage[2]}" that does not exist for namespace "{spage[1]}".'
        return None

    @staticmethod
    def page_ondisk_name(page: str) -> str:
        return None

    @staticmethod
    def get_used_on_pages(page: str) -> list:
        return []

    @classmethod
    def get_create_page_name(cls, page: str) -> str:
        assert page.startswith("Folder/")
        assert page.endswith("/Main Page")

        if cls._is_root(page):
            return ""
        if cls._is_namespace_root(page):
            return ""

        page = page[len("Folder/") : -len("/Main Page")]
        if page.startswith("Page/"):
            page = page[len("Page/") :]
        return f"{page}/"

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        return content.add_content(page)


wiki_page.register_namespace(Namespace)
