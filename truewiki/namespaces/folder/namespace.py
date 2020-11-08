import logging

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
    def page_is_valid(cls, page: str) -> bool:
        assert page.startswith("Folder/")
        spage = page.split("/")

        if cls._is_root(page):
            return True
        if cls._is_namespace_root(page):
            return singleton.STORAGE.dir_exists(spage[1])

        # There should always be a namespace and language code in the path.
        if len(spage) < 4:
            return False
        # The namespace and language should already exist.
        return singleton.STORAGE.dir_exists(f"{spage[1]}/{spage[2]}")

    @staticmethod
    def page_ondisk_name(page: str) -> str:
        return None

    @staticmethod
    def get_used_on_pages(page: str) -> list:
        return None

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
        return f"{page}/?newpage"

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        return content.add_content(page)


wiki_page.register_namespace(Namespace)
