import logging
import os

from typing import Optional

from . import content
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
    namespace = "File"
    force_link = ":File:"

    @staticmethod
    def _is_root(page: str) -> bool:
        return page == "File/Main Page"

    @staticmethod
    def _is_language_root(page: str) -> bool:
        return page.endswith("/Main Page") and len(page.split("/")) == 3

    @staticmethod
    def _is_root_of_folder(page: str) -> bool:
        return page.endswith("/Main Page")

    @classmethod
    def page_load(cls, page: str) -> str:
        assert page.startswith("File/")

        if cls._is_root(page):
            return "A list of all the languages which have one or more files."

        if cls._is_language_root(page):
            return "All the files that belong to this language."
        if cls._is_root_of_folder(page):
            return "All the files that belong to this folder."

        filename = f"{singleton.STORAGE.folder}/{page}.mediawiki"
        if not os.path.exists(filename):
            return "There is currently no file with that name."

        with open(filename) as fp:
            body = fp.read()
        return body

    @classmethod
    def page_exists(cls, page: str) -> bool:
        assert page.startswith("File/")

        if cls._is_root(page):
            return True

        if cls._is_root_of_folder(page):
            page = page[: -len("Main Page")]
            return os.path.isdir(f"{singleton.STORAGE.folder}/{page}")

        return os.path.exists(f"{singleton.STORAGE.folder}/{page}.mediawiki")

    @classmethod
    def page_is_valid(cls, page: str) -> bool:
        assert page.startswith("File/")
        spage = page.split("/")

        if cls._is_root(page):
            return True

        # There should always be a language code in the path.
        if len(spage) < 3:
            return False
        # The language should already exist.
        if not os.path.isdir(f"{singleton.STORAGE.folder}/File/{spage[1]}"):
            return False

        return True

    @staticmethod
    def get_used_on_pages(page: str) -> list:
        assert page.startswith("File/")
        return metadata.FILES[page[len("File/"):]]

    @classmethod
    def has_source(cls, page: str) -> bool:
        return not cls._is_root(page) and not cls._is_root_of_folder(page)

    @classmethod
    def get_create_page_name(cls, page: str) -> str:
        assert page.startswith("File/")

        if not cls._is_root_of_folder(page):
            return ""
        if cls._is_root(page):
            return ""

        page = page[: -len("/Main Page")]
        return f"{page}/?newpage"

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return language_bar.create(instance, page)

    @classmethod
    def add_content(cls, instance: wiki_page.WikiPage, page: str) -> str:
        assert page.startswith("File/")

        if cls._is_root(page):
            return folder_content.add_content("Folder/File/Main Page", namespace="File", folder_label="Languages")
        if cls._is_root_of_folder(page):
            return folder_content.add_content(
                f"Folder/{page}", namespace="File", namespace_for_folder=True, page_label="Files"
            )

        if os.path.exists(f"{singleton.STORAGE.folder}/{page}"):
            return content.add_content(page)
        return ""

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        footer = ""
        footer += category_footer.add_footer(instance, page)
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

    @staticmethod
    def add_edit_content() -> str:
        return """
<hr />
Upload new file: <input type="file" name="file" />
<p>Please ensure the upload has a license that is compatible with the license of this wiki.</p>
<p>Any new upload will overwrite the existing upload at this location. Preview won't work for new uploads.</p>
<hr />
        """

    @staticmethod
    def edit_callback(page: str, payload, execute: bool = False):
        if not payload.get("file"):
            return None

        payload["file"].file.seek(0)
        data = payload["file"].file.read()

        if payload["file"].content_type == "image/png":
            # See http://www.libpng.org/pub/png/spec/1.2/PNG-Rationale.html#R.PNG-file-signature
            if not data.startswith(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"):
                return f'Uploaded file "{payload["file"].filename}" is not a valid PNG image.'
        elif payload["file"].content_type == "image/jpeg":
            # See https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format#File_format_structure
            if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
                return f'Uploaded file "{payload["file"].filename}" is not a valid JPEG image.'
        else:
            return f'Uploaded file "{payload["file"].filename}" is not a valid image. Only PNG and JPEG is supported.'

        if execute:
            with open(f"{singleton.STORAGE.folder}/{page}", "wb") as fp:
                fp.write(data)

        return None

    @staticmethod
    def edit_rename(old_page: str, new_page: str):
        assert old_page.startswith("File/")
        assert new_page.startswith("File/")

        os.rename(f"{singleton.STORAGE.folder}/{old_page}", f"{singleton.STORAGE.folder}/{new_page}")

wiki_page.register_namespace(Namespace, default_file=True)
