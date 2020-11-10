import html
import logging
import urllib

from typing import Optional

from .. import base
from ..category import footer as category_footer
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
    namespace = "Template"
    force_link = ":Template:"

    @staticmethod
    def _is_root(page: str) -> bool:
        return page == "Template/Main Page"

    @staticmethod
    def _is_language_root(page: str) -> bool:
        return page.endswith("/Main Page") and len(page.split("/")) == 3

    @staticmethod
    def _is_root_of_folder(page: str) -> bool:
        return page.endswith("/Main Page")

    @classmethod
    def page_load(cls, page: str) -> str:
        assert page.startswith("Template/")

        if cls._is_root(page):
            return "A list of all the languages which have one or more templates."

        if cls._is_language_root(page):
            return "All the templates that belong to this language."

        if not singleton.STORAGE.file_exists(f"{page}.mediawiki"):
            return "There is currently no text on this page."

        body = singleton.STORAGE.file_read(f"{page}.mediawiki")

        if not body:
            return "There is currently no text on this page."

        return body

    @classmethod
    def page_exists(cls, page: str) -> bool:
        assert page.startswith("Template/")

        if cls._is_root(page):
            return True

        if cls._is_language_root(page):
            return singleton.STORAGE.dir_exists(f"Template/{page.split('/')[1]}")

        return singleton.STORAGE.file_exists(f"{page}.mediawiki")

    @staticmethod
    def get_used_on_pages(page: str) -> list:
        assert page.startswith("Template/")
        page = page[len("Template/") :]
        return metadata.TEMPLATES[f"Template/{page}"] + metadata.LINKS[f":Template:{page}"]

    @classmethod
    def page_is_valid(cls, page: str, is_new_page: bool) -> Optional[str]:
        assert page.startswith("Template/")
        spage = page.split("/")

        if cls._is_root(page):
            return None

        if is_new_page and cls._is_language_root(page):
            return f'Page name "{page}" is invalid, as it is automatically generated.'

        # There should always be a language code in the path.
        if len(spage) < 3:
            return f'Page name "{page}" is missing a language code.'
        # The language should already exist.
        if not singleton.STORAGE.dir_exists(f"Template/{spage[1]}"):
            return f'Page name "{page}" is in language "{spage[1]}" that does not exist.'

        return None

    @classmethod
    def has_source(cls, page: str) -> bool:
        return not cls._is_root(page) and not cls._is_language_root(page)

    @classmethod
    def get_create_page_name(cls, page: str) -> str:
        assert page.startswith("Template/")

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
        assert page.startswith("Template/")

        if cls._is_root(page):
            return folder_content.add_content("Folder/Template/Main Page", namespace="Template")
        if cls._is_language_root(page):
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
        filename = f"Template/{template}.mediawiki"
        if not singleton.STORAGE.file_exists(filename):
            href = urllib.parse.quote(template)
            template = html.escape(template)
            return f'<a class="new" href="/Template/{href}" title="{template}">Template:{template}</a>'

        return singleton.STORAGE.file_read(filename)

    @staticmethod
    def template_exists(template: str) -> bool:
        return singleton.STORAGE.file_exists(f"Template/{template}.mediawiki")

    @classmethod
    def template_is_valid(cls, template: str) -> Optional[str]:
        return cls.page_is_valid(f"Template/{template}", False)


wiki_page.register_namespace(Namespace, default_template=True)
