import logging
import os

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

    @staticmethod
    def page_load(page: str) -> str:
        assert page.startswith("Folder/")

        if Namespace._is_root(page):
            return "A list of all namespaces with files and folders."

        if Namespace._is_namespace_root(page):
            return "A list of all the languages within this namespace."

        return "All the pages and folders inside this folder."

    @staticmethod
    def page_exists(page: str) -> bool:
        assert page.startswith("Folder/")

        if Namespace._is_root(page):
            return True

        if not page.endswith("/Main Page"):
            return False

        page = page[len("Folder/") : -len("/Main Page")]
        return os.path.isdir(f"{singleton.STORAGE.folder}/{page}")

    @staticmethod
    def page_is_valid(page: str) -> bool:
        assert page.startswith("Folder/")
        spage = page.split("/")

        if Namespace._is_root(page):
            return True
        if Namespace._is_namespace_root(page):
            return os.path.isdir(f"{singleton.STORAGE.folder}/{spage[1]}")

        # There should always be a namespace and language code in the path.
        if len(spage) < 4:
            return False
        # The namespace and language should already exist.
        return os.path.isdir(f"{singleton.STORAGE.folder}/{spage[1]}/{spage[2]}")

    @staticmethod
    def page_ondisk_name(page: str) -> str:
        return None

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        return content.add_content(page)


wiki_page.register_namespace(Namespace)
