import logging
import os

from .. import base
from ..category import footer as category_footer
from ..folder import (
    content as folder_content,
    footer as folder_footer,
)
from ... import (
    singleton,
    wiki_page,
)
from ...content import language_bar

log = logging.getLogger(__name__)


class Namespace(base.Namespace):
    namespace = "Template"
    force_link = ":Template:"

    @staticmethod
    def _is_root(page: str) -> bool:
        return page == "Template/Main Page"

    @staticmethod
    def _is_language_root(page: str) -> bool:
        return page.endswith("/Main Page") and len(page.split("/")) == 3

    @staticmethod
    def page_load(page: str) -> str:
        assert page.startswith("Template/")

        if Namespace._is_root(page):
            return "A list of all the languages which have one or more templates."

        if Namespace._is_language_root(page):
            return "All the templates that belong to this language."

        filename = f"{singleton.STORAGE.folder}/{page}.mediawiki"
        if not os.path.exists(filename):
            return "There is currently no text on this page."

        with open(filename) as fp:
            body = fp.read()
        return body

    @staticmethod
    def page_exists(page: str) -> bool:
        assert page.startswith("Template/")

        if Namespace._is_root(page):
            return True

        if Namespace._is_language_root(page):
            return os.path.isdir(f"{singleton.STORAGE.folder}/Template/{page.split('/')[1]}")

        return os.path.exists(f"{singleton.STORAGE.folder}/{page}.mediawiki")

    @staticmethod
    def page_is_valid(page: str) -> bool:
        assert page.startswith("Template/")
        spage = page.split("/")

        if Namespace._is_root(page):
            return True

        # There should always be a language code in the path.
        if len(spage) < 3:
            return False
        # The language should already exist.
        if not os.path.isdir(f"{singleton.STORAGE.folder}/Template/{spage[1]}"):
            return False

        return True

    @staticmethod
    def has_source(page: str) -> bool:
        return not Namespace._is_root(page) and not Namespace._is_language_root(page)

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return language_bar.create(instance, page)

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        assert page.startswith("Template/")

        if Namespace._is_root(page):
            return folder_content.add_content("Folder/Template/Main Page", namespace="Template")
        if Namespace._is_language_root(page):
            language = page.split("/")[1]
            return folder_content.add_content(f"Folder/Template/{language}/Main Page", namespace="Template")

        return ""

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        footer = ""
        footer += category_footer.add_footer(instance, page)
        footer += folder_footer.add_footer(page, "Template")
        return footer

    @staticmethod
    def template_load(template: str) -> str:
        filename = f"{singleton.STORAGE.folder}/Template/{template}.mediawiki"
        if not os.path.exists(filename):
            return f'<a href="/Template/{template}" title="{template}">Template/{template}</a>'

        with open(filename) as fp:
            return fp.read()

    @staticmethod
    def template_exists(template: str) -> bool:
        return os.path.exists(f"{singleton.STORAGE.folder}/Template/{template}.mediawiki")


wiki_page.register_namespace(Namespace, default_template=True)
