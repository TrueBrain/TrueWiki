import logging

from typing import Optional

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

    @classmethod
    def page_load(cls, page: str) -> str:
        assert page.startswith("Category/")

        if cls._is_root(page):
            return "A list of all the languages which have one or more categories."

        if cls._is_language_root(page):
            return "All the categories that belong to this language."
        if cls._is_root_of_folder(page):
            return "All the categories that belong to this folder."

        filename = f"{page}.mediawiki"
        if not singleton.STORAGE.file_exists(filename):
            return "There is currently no additional text for this category."

        body = singleton.STORAGE.file_read(filename)

        if not body:
            return "There is currently no additional text for this category."

        return body

    @classmethod
    def page_exists(cls, page: str) -> bool:
        assert page.startswith("Category/")

        if cls._is_root(page):
            return True

        if cls._is_root_of_folder(page):
            page = page[: -len("Main Page")]
            return singleton.STORAGE.dir_exists(page)

        # If we know the category, the page exists; it might not have a
        # .mediawiki file (yet), but the page still exists.
        if page[len("Category/") :] in metadata.CATEGORIES:
            return True

        # The category is empty but if there is a mediawiki file for it, it
        # is also a valid category.
        return singleton.STORAGE.file_exists(f"{page}.mediawiki")

    @classmethod
    def page_is_valid(cls, page: str, is_new_page: bool) -> Optional[str]:
        assert page.startswith("Category/")
        spage = page.split("/")

        if cls._is_root(page):
            return None

        if is_new_page and cls._is_language_root(page):
            return f'Page name "{page}" is invalid, as it is automatically generated.'

        # There should always be a language code in the path.
        if len(spage) < 3:
            return f'Page name "{page}" is missing a language code.'
        # The language should already exist.
        if not singleton.STORAGE.dir_exists(f"Category/{spage[1]}"):
            return f'Page name "{page}" is in language "{spage[1]}" that does not exist.'

        return None

    @classmethod
    def has_source(cls, page: str) -> bool:
        return not cls._is_root(page) and not cls._is_root_of_folder(page)

    @classmethod
    def get_create_page_name(cls, page: str) -> str:
        assert page.startswith("Category/")

        if not cls._is_root_of_folder(page):
            return ""
        if cls._is_root(page):
            return ""

        page = page[: -len("/Main Page")]
        return f"{page}/"

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return language_bar.create(instance, page)

    @classmethod
    def add_content(cls, instance: wiki_page.WikiPage, page: str) -> str:
        assert page.startswith("Category/")

        if cls._is_root(page):
            return folder_content.add_content(
                "Folder/Category/Main Page", namespace="Category", folder_label="Languages"
            )
        if cls._is_root_of_folder(page):
            return folder_content.add_content(
                f"Folder/{page}", namespace="Category", namespace_for_folder=True, page_label="Categories"
            )

        return content.add_content(page)

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        content = footer.add_footer(instance, page)
        content += folder_footer.add_footer(page, "Category")
        return content


wiki_page.register_namespace(Namespace)
