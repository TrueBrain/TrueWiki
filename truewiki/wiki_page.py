import logging
import unicodedata

from typing import Optional
from wikitexthtml import Page
from wikitexthtml.exceptions import (
    InvalidWikiLink,
    InvalidTemplate,
)

log = logging.getLogger(__name__)


NAMESPACES = {}
NAMESPACE_DEFAULT_PAGE = None
NAMESPACE_DEFAULT_TEMPLATE = None
NAMESPACE_DEFAULT_FILE = None
NAMESPACE_MAPPING = {}

DISALLOWED_NAMES = (
    ":",  # Namespace indicator.
    "|",  # Just .. don't.
    "#",  # Makes hash-parts of URLs difficult.
    "[",  # wikitext syntax.
    "]",  # wikitext syntax.
    "{",  # wikitext syntax.
    "}",  # wikitext syntax.
    "_",  # Use a space instead.
    "<",  # Reserved character on NTFS.
    ">",  # Reserved character on NTFS.
    "\\",  # Reserved character on NTFS.
    '"',  # Reserved character on NTFS.
    "*",  # Reserved character on NTFS.
    "?",  # Reserved character on NTFS.
)

# "fmt: off" can be removed if we ever add a second entry.
# fmt: off
DISALLOWS_PARTS_LEADING = (
    ".",  # Don't allow "hidden" files.
)
# fmt: on


def _check_illegal_names(page: str) -> Optional[str]:
    for disallowed_name in DISALLOWED_NAMES:
        if disallowed_name in page:
            return f'Page name "{page}" contains "{disallowed_name}", which is not allowed.'

    if page.startswith("/"):
        return f'Page name "{page}" starts with a "/", which is not allowed.'

    # Check the parts of the page, ignoring a trailing /.
    # A trailing / is allowed, as it will load the "Main Page" instead.
    for part in page.rstrip("/").split("/"):
        if not part:
            return f'Page name "{page}" contains a folder that is empty, which is not allowed.'

        if part.startswith(DISALLOWS_PARTS_LEADING):
            return f'Page name "{page}" contains a filename/folder that starts with a dot, which is not allowed.'

        if part.strip() != part:
            return f'Page name "{page}" contains a filename/folder that starts/ends with a space, which is not allowed.'

    for letter in page:
        if unicodedata.category(letter)[0] == "C":
            return (
                f'Page name "{page}" contains '
                '<a href="https://en.wikipedia.org/wiki/Control_character" target="_new">Control Characters</a>, '
                "which is not allowed."
            )

    return None


class WikiPage(Page):
    def __init__(self, page: str) -> None:
        super().__init__(page)
        self.en_page = None
        self.categories = []

    def page_load(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_load(page)

    def page_exists(self, page: str) -> bool:
        # "License" is a special page that always exists.
        if page == "License":
            return True

        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_exists(page)

    def page_ondisk_name(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_ondisk_name(page)

    def page_is_valid(self, page: str, is_new_page: bool = False) -> Optional[str]:
        # "License" is a special page that always exists.
        if page == "License":
            return None

        error = _check_illegal_names(page)
        if error:
            return error

        if "/" not in page:
            return f'Page name "{page}" is missing either a language or a namespace.'

        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_is_valid(page, is_new_page)

    def page_get_correct_case(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_get_correct_case(page)

    def has_source(self, page: str) -> bool:
        # "License" is a special page, of which we never show the source.
        if page == "License":
            return False

        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).has_source(page)

    def has_history(self, page: str) -> bool:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).has_history(page)

    def get_create_page_name(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).get_create_page_name(page)

    def get_used_on_pages(self) -> str:
        namespace = self.page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).get_used_on_pages(self.page)

    def clean_title(self, title: str) -> str:
        # "License" is a special page that is called "License"
        if title == "License":
            return "License"

        error = self.page_is_valid(title)
        if error:
            raise InvalidWikiLink(error)

        namespace = title.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).clean_title(self.page, title)

    def add_language(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).add_language(self, page)

    def add_content(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).add_content(self, page)

    def add_footer(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).add_footer(self, page)

    def add_edit_content(self) -> str:
        namespace = self.page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).add_edit_content()

    def edit_callback(self, old_page: str, new_page: str, payload, execute: bool = False) -> str:
        namespace = old_page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).edit_callback(old_page, new_page, payload, execute)

    def edit_rename(self, old_page: str, new_page: str) -> str:
        namespace = old_page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).edit_rename(old_page, new_page)

    def template_load(self, template: str) -> str:
        if ":" in template:
            namespace, _, template = template.partition(":")
        else:
            namespace = None

        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_TEMPLATE).template_load(template)

    def template_exists(self, template: str) -> bool:
        error = self.template_is_valid(template)
        if error:
            raise InvalidTemplate(error)

        if ":" in template:
            namespace, _, template = template.partition(":")
        else:
            namespace = None

        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_TEMPLATE).template_exists(template)

    def template_is_valid(self, template: str) -> Optional[str]:
        if ":" in template:
            namespace, _, template = template.partition(":")
        else:
            namespace = None

        error = _check_illegal_names(template)
        if error:
            return error

        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_TEMPLATE).template_is_valid(template)

    def file_exists(self, file: str) -> bool:
        error = self.file_is_valid(file)
        if error:
            raise InvalidWikiLink(error)

        return NAMESPACE_DEFAULT_FILE.file_exists(file)

    def file_is_valid(self, file: str) -> Optional[str]:
        error = _check_illegal_names(file)
        if error:
            return error

        return NAMESPACE_DEFAULT_FILE.file_is_valid(file)

    def file_get_link(self, url: str) -> str:
        return NAMESPACE_DEFAULT_FILE.file_get_link(url)

    def file_get_img(self, url: str, thumb: Optional[int] = None) -> str:
        return NAMESPACE_DEFAULT_FILE.file_get_img(url, thumb)

    def clean_url(self, url: str) -> str:
        if url.endswith("Main Page"):
            return url[: -len("Main Page")]
        return url


def register_namespace(namespace, default_page=False, default_template=False, default_file=False):
    global NAMESPACE_DEFAULT_PAGE, NAMESPACE_DEFAULT_TEMPLATE, NAMESPACE_DEFAULT_FILE

    NAMESPACES[namespace.namespace] = namespace
    NAMESPACE_MAPPING[f"{namespace.namespace}/"] = namespace.force_link
    if default_page:
        NAMESPACE_DEFAULT_PAGE = namespace
    if default_template:
        NAMESPACE_DEFAULT_TEMPLATE = namespace
    if default_file:
        NAMESPACE_DEFAULT_FILE = namespace
