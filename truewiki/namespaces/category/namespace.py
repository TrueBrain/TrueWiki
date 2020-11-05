import logging
import os

from . import (
    content,
    footer,
)
from .. import base
from ..folder import (
    content as folder_content,
    footer as folder_footer,
)
from ... import (
    metadata,
    singleton,
    wiki_page,
)
from ...content import language_bar

log = logging.getLogger(__name__)


class Namespace(base.Namespace):
    namespace = "Category"
    force_link = ":Category:"

    @staticmethod
    def _is_root(page: str) -> bool:
        return page == "Category/Main Page"

    @staticmethod
    def _is_language_root(page: str) -> bool:
        return page.endswith("/Main Page") and len(page.split("/")) == 3

    @staticmethod
    def _is_root_of_folder(page: str) -> bool:
        return page.endswith("/Main Page")

    @staticmethod
    def page_load(page: str) -> str:
        assert page.startswith("Category/")

        if Namespace._is_root(page):
            return "A list of all the languages which have one or more categories."

        if Namespace._is_language_root(page):
            return "All the categories that belong to this language."
        if Namespace._is_root_of_folder(page):
            return "All the categories that belong to this folder."

        filename = f"{singleton.STORAGE.folder}/{page}.mediawiki"
        if not os.path.exists(filename):
            return "There is currently no additional text for this category."

        with open(filename) as fp:
            body = fp.read()
        return body

    @staticmethod
    def page_exists(page: str) -> bool:
        assert page.startswith("Category/")

        if Namespace._is_root(page):
            return True

        if Namespace._is_root_of_folder(page):
            page = page[:-len("Main Page")]
            return os.path.isdir(f"{singleton.STORAGE.folder}/{page}")

        # If we know the category, the page exists; it might not have a
        # .mediawiki file (yet), but the page still exists.
        if page[len("Category/") :] in metadata.CATEGORIES:
            return True

        # The category is empty but if there is a mediawiki file for it, it
        # is also a valid category.
        return os.path.exists(f"{singleton.STORAGE.folder}/{page}.mediawiki")

    @staticmethod
    def page_is_valid(page: str) -> bool:
        assert page.startswith("Category/")
        spage = page.split("/")

        if Namespace._is_root(page):
            return True

        # There should always be a language code in the path.
        if len(spage) < 3:
            return False
        # The language should already exist.
        if not os.path.isdir(f"{singleton.STORAGE.folder}/Category/{spage[1]}"):
            return False

        return True

    @staticmethod
    def has_source(page: str) -> bool:
        return not Namespace._is_root(page) and not Namespace._is_root_of_folder(page)

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return language_bar.create(instance, page)

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        assert page.startswith("Category/")

        if Namespace._is_root(page):
            return folder_content.add_content("Folder/Category/Main Page", namespace="Category", folder_label="Languages")
        if Namespace._is_root_of_folder(page):
            return folder_content.add_content(f"Folder/{page}", namespace="Category", namespace_for_folder=True, page_label="Categories")

        return content.add_content(page)

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        content = footer.add_footer(instance, page)
        content += folder_footer.add_footer(page, "Category")
        return content


wiki_page.register_namespace(Namespace)
