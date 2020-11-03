import logging
import os

from .. import base
from ..category import footer as category_footer
from ..folder import footer as folder_footer
from ... import (
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
        filename = f"{singleton.STORAGE.folder}/Page/{page}.mediawiki"

        if not os.path.exists(filename):
            return ""

        with open(filename) as fp:
            body = fp.read()
        return body

    @staticmethod
    def page_exists(page: str) -> bool:
        return os.path.exists(f"{singleton.STORAGE.folder}/Page/{page}.mediawiki")

    @staticmethod
    def page_ondisk_name(page: str) -> str:
        return f"Page/{page}.mediawiki"

    @staticmethod
    def has_source(page: str) -> bool:
        return Namespace.page_exists(page)

    @staticmethod
    def has_history(page: str) -> bool:
        return Namespace.page_exists(page)

    @classmethod
    def clean_title(cls, title: str) -> str:
        title = super().clean_title(title)

        if title == "Page":
            return "OpenTTD's Wiki"

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
        filename = f"{singleton.STORAGE.folder}/Page/{template}.mediawiki"
        if not os.path.exists(filename):
            return f'<a href="/{template}" title="{template}">Page:{template}</a>'

        with open(filename) as fp:
            return fp.read()

    @staticmethod
    def template_exists(template: str) -> bool:
        return os.path.exists(f"{singleton.STORAGE.folder}/Page/{template}.mediawiki")


wiki_page.register_namespace(Namespace, default_page=True)
