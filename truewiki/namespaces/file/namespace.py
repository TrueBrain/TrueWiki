import logging
import os

from typing import Optional

from . import content
from .. import base
from ..folder import (
    content as folder_content,
    footer as folder_footer,
)
from ... import (
    singleton,
    wiki_page,
)

log = logging.getLogger(__name__)


class Namespace(base.Namespace):
    namespace = "File"
    force_link = ":File:"

    @staticmethod
    def _is_root(page: str) -> bool:
        return page == "File/Main Page"

    @staticmethod
    def _is_language_root(page: str) -> bool:
        return page.endswith("/Main Page") and len(page.split("/")) == 3

    @staticmethod
    def page_load(page: str) -> str:
        assert page.startswith("File/")

        if Namespace._is_root(page):
            return "A list of all the languages which have one or more files."

        if Namespace._is_language_root(page):
            return "All the files that belong to this language."

        filename = f"{singleton.STORAGE.folder}/{page}.mediawiki"
        if not os.path.exists(filename):
            return "There is currently no file with that name."

        with open(filename) as fp:
            body = fp.read()
        return body

    @staticmethod
    def page_exists(page: str) -> bool:
        assert page.startswith("File/")

        if Namespace._is_root(page):
            return True

        if Namespace._is_language_root(page):
            return os.path.isdir(f"{singleton.STORAGE.folder}/File/{page.split('/')[1]}")

        return os.path.exists(f"{singleton.STORAGE.folder}/{page}.mediawiki")

    @staticmethod
    def has_source(page: str) -> bool:
        return not Namespace._is_root(page) and not Namespace._is_language_root(page)

    @staticmethod
    def has_history(page: str) -> bool:
        return Namespace.page_exists(page)

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        assert page.startswith("File/")

        if Namespace._is_root(page):
            return folder_content.add_content("Folder/File/Main Page", namespace="File")
        if Namespace._is_language_root(page):
            language = page.split("/")[1]
            return folder_content.add_content(f"Folder/File/{language}/Main Page", namespace="File")

        return content.add_content(page)

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        footer = ""
        footer += folder_footer.add_footer(page, "File")
        return footer

    @staticmethod
    def file_exists(file: str) -> bool:
        return os.path.exists(f"{singleton.STORAGE.folder}/File/{file}")

    @staticmethod
    def file_get_link(url: str) -> str:
        return f"/File/{url}"

    @staticmethod
    def file_get_img(url: str, thumb: Optional[int]) -> str:
        # TODO -- Support thumb sizes
        return f"/uploads/{url}"


wiki_page.register_namespace(Namespace, default_file=True)
