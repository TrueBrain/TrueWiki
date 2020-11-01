import logging
import os

from . import (
    content_language_root,
    content_root,
    content,
    footer,
)
from .. import base
from ..folder import footer as folder_footer
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
    def page_load(page: str) -> str:
        assert page.startswith("Category/")

        if Namespace._is_root(page):
            return "A list of all the languages which have one or more categories."

        if Namespace._is_language_root(page):
            return "All the categories that belong to this language"

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

        if Namespace._is_language_root(page):
            return os.path.isdir(f"{singleton.STORAGE.folder}/Category/{page.split('/')[1]}")

        # If we know the category, the page exists; it might not have a
        # .mediawiki file (yet), but the page still exists.
        if page[len("Category/") :] in metadata.CATEGORIES:
            return True

        # The category is empty but if there is a mediawiki file for it, it
        # is also a valid category.
        return os.path.exists(f"{singleton.STORAGE.folder}/{page}.mediawiki")

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return language_bar.create(instance, page)

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        assert page.startswith("Category/")

        if Namespace._is_root(page):
            return content_root.add_content(page)
        if Namespace._is_language_root(page):
            return content_language_root.add_content(page)
        return content.add_content(page)

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        content = footer.add_footer(instance, page)
        content += folder_footer.add_footer(page, "Category")
        return content


wiki_page.register_namespace(Namespace)
