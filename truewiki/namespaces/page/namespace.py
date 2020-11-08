import logging

from .. import base
from ..category import footer as category_footer
from ..folder import footer as folder_footer
from ... import (
    metadata,
    singleton,
    wiki_page,
)
from ...content import language_bar

log = logging.getLogger(__name__)


class Namespace(base.Namespace):
    namespace = "Page"
    force_link = ""

    @staticmethod
    def page_load(page: str) -> str:
        filename = f"Page/{page}.mediawiki"

        if not singleton.STORAGE.file_exists(filename):
            return "There is currently no text on this page."

        return singleton.STORAGE.file_read(filename)

    @staticmethod
    def page_exists(page: str) -> bool:
        return singleton.STORAGE.file_exists(f"Page/{page}.mediawiki")

    @staticmethod
    def page_ondisk_name(page: str) -> str:
        return f"Page/{page}.mediawiki"

    @staticmethod
    def get_used_on_pages(page: str) -> list:
        return metadata.TEMPLATES[f"Page/{page}"]

    @staticmethod
    def page_is_valid(page: str) -> bool:
        spage = page.split("/")

        # There should always be a language code in the path.
        if len(spage) < 2:
            return False
        # The language should already exist.
        if not singleton.STORAGE.dir_exists(f"Page/{spage[0]}"):
            return False

        return True

    @classmethod
    def page_get_correct_case(cls, page: str) -> str:
        correct_page = super().page_get_correct_case(f"Page/{page}")
        if correct_page.startswith("Page/"):
            correct_page = correct_page[len("Page/") :]
        return correct_page

    @staticmethod
    def has_source(page: str) -> bool:
        return True

    @classmethod
    def clean_title(cls, page: str, title: str) -> str:
        title = super().clean_title(page, title, root_name="OpenTTD's Wiki")
        return title

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return language_bar.create(instance, page)

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        footer = ""
        footer += category_footer.add_footer(instance, page)
        footer += folder_footer.add_footer(page, "Page")
        return footer

    @staticmethod
    def template_load(template: str) -> str:
        filename = f"Page/{template}.mediawiki"
        if not singleton.STORAGE.file_exists(filename):
            return f'<a href="/{template}" title="{template}">Page:{template}</a>'

        return singleton.STORAGE.file_read(filename)

    @staticmethod
    def template_exists(template: str) -> bool:
        return singleton.STORAGE.file_exists(f"Page/{template}.mediawiki")


wiki_page.register_namespace(Namespace, default_page=True)
