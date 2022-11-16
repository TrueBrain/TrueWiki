import logging

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

        filename = f"{page}.mediawiki"
        if not singleton.STORAGE.file_exists(filename):
            return "There is currently no file with that name."

        body = singleton.STORAGE.file_read(filename)

        if not body:
            return "This file has no description yet."

        return body

    @classmethod
    def page_exists(cls, page: str) -> bool:
        assert page.startswith("File/")

        if cls._is_root(page):
            return True

        if cls._is_root_of_folder(page):
            page = page[: -len("Main Page")]
            return singleton.STORAGE.dir_exists(page)

        return singleton.STORAGE.file_exists(f"{page}.mediawiki")

    @classmethod
    def page_is_valid(cls, page: str, is_new_page: bool) -> Optional[str]:
        assert page.startswith("File/")
        spage = page.split("/")

        if cls._is_root(page):
            return

        if is_new_page and cls._is_language_root(page):
            return f'Page name "{page}" is invalid, as it is automatically generated.'
        if is_new_page and cls._is_root_of_folder(page):
            return f'Page name "{page}" is invalid, as it is automatically generated.'

        # There should always be a language code in the path.
        if len(spage) < 3:
            return f'Page name "{page}" is missing a language code.'
        # The language should already exist.
        if spage[1] not in metadata.LANGUAGES:
            return f'Page name "{page}" is in language "{spage[1]}" that does not exist.'

        if not cls._is_language_root(page) and not cls._is_root_of_folder(page):
            if not page.endswith((".png", ".jpeg", ".gif")):
                return f'Page name "{page}" in the File namespace should end with either ".png", ".gif", or ".jpeg".'

        return None

    @classmethod
    def page_get_language(cls, page: str) -> Optional[str]:
        assert page.startswith("File/")

        if cls._is_root(page):
            return None

        return page.split("/")[1]

    @staticmethod
    def get_used_on_pages(page: str) -> list:
        assert page.startswith("File/")
        page = page[len("File/") :]
        return metadata.FILES[page] + metadata.LINKS[f":File:{page}"]

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
        return f"{page}/"

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return language_bar.create(instance, page)

    @classmethod
    def add_content(cls, instance: wiki_page.WikiPage, page: str) -> str:
        assert page.startswith("File/")

        if cls._is_root(page):
            return folder_content.add_language_content("File")
        if cls._is_root_of_folder(page):
            return folder_content.add_content(
                f"Folder/{page}", namespace="File", namespace_for_folder=True, page_label="Files"
            )

        if singleton.STORAGE.file_exists(f"{page}"):
            return content.add_content(page)

        if cls.page_exists(page):
            return "<hr /><small>(no file uploaded yet)</small>"

        return ""

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        footer = ""
        footer += category_footer.add_footer(instance, page)
        footer += folder_footer.add_footer(page, "File")
        return footer

    @staticmethod
    def file_exists(file: str) -> bool:
        return singleton.STORAGE.file_exists(f"File/{file}")

    @classmethod
    def file_is_valid(cls, file: str) -> Optional[str]:
        return cls.page_is_valid(f"File/{file}", False)

    @staticmethod
    def file_get_link(url: str) -> str:
        return f"/File/{url}"

    @staticmethod
    def file_get_img(url: str, thumb: Optional[int] = None) -> str:
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
    def edit_callback(old_page: str, new_page: str, payload, execute: bool = False):
        if old_page.split(".")[-1] != new_page.split(".")[-1]:
            return "Cannot rename extension of a file."

        # Someone is renaming the File to another namespace. This is most
        # likely not what the user wants, but let him do it anyway.
        if not new_page.startswith("File/"):
            return None

        # Someone is making a File without adding a file. This is not ideal,
        # but for the same reason as the case above, we let him do it anyway.
        if not payload.get("file"):
            return None

        payload["file"].file.seek(0)
        data = payload["file"].file.read()

        if payload["file"].content_type == "image/png":
            # See http://www.libpng.org/pub/png/spec/1.2/PNG-Rationale.html#R.PNG-file-signature
            if not data.startswith(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"):
                return f'Uploaded file "{payload["file"].filename}" is not a valid PNG image.'

            if not new_page.endswith(".png"):
                return f'Page name "{new_page}" should end with ".png" if uploading a PNG.'
        elif payload["file"].content_type == "image/jpeg":
            # See https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format#File_format_structure
            if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
                return f'Uploaded file "{payload["file"].filename}" is not a valid JPEG image.'

            if not new_page.endswith(".jpeg"):
                return f'Page name "{new_page}" should end with ".jpeg" if uploading a JPEG.'
        elif payload["file"].content_type == "image/gif":
            # See https://en.wikipedia.org/wiki/GIF#File_format
            if not data.startswith(b"GIF87a") and not data.startswith(b"GIF89a"):
                return f'Uploaded file "{payload["file"].filename}" is not a valid GIF image.'

            if not new_page.endswith(".gif"):
                return f'Page name "{new_page}" should end with ".gif" if uploading a GIF.'
        else:
            return (
                f'Uploaded file "{payload["file"].filename}" is not a valid image. '
                "Only PNG, GIF, and JPEG is supported."
            )

        if execute:
            singleton.STORAGE.file_write(new_page, data, "wb")

        return None

    @staticmethod
    def edit_rename(old_page: str, new_page: str):
        assert old_page.startswith("File/")

        # If the old file didn't exist, it is a File without a file. We don't
        # have to do anything for the rename.
        if not singleton.STORAGE.file_exists(old_page):
            return

        # If we move the page outside of File, remove the file.
        if not new_page.startswith("File/"):
            singleton.STORAGE.file_remove(old_page)
            return

        singleton.STORAGE.file_rename(old_page, new_page)


wiki_page.register_namespace(Namespace, default_file=True)
