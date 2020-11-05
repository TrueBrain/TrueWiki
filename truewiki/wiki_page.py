import logging

from typing import Optional
from wikitexthtml import Page

log = logging.getLogger(__name__)


NAMESPACES = {}
NAMESPACE_DEFAULT_PAGE = None
NAMESPACE_DEFAULT_TEMPLATE = None
NAMESPACE_DEFAULT_FILE = None
NAMESPACE_MAPPING = {}


class WikiPage(Page):
    def __init__(self, page: str) -> None:
        super().__init__(page)
        self.en_page = None
        self.categories = []

    def page_load(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_load(page)

    def page_exists(self, page: str) -> bool:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_exists(page)

    def page_ondisk_name(self, page: str) -> str:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_ondisk_name(page)

    def page_is_valid(self, page: str) -> bool:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).page_is_valid(page)

    def has_source(self, page: str) -> bool:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).has_source(page)

    def has_history(self, page: str) -> bool:
        namespace = page.split("/")[0]
        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_PAGE).has_history(page)

    def clean_title(self, title: str) -> str:
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

    def template_load(self, template: str) -> str:
        if ":" in template:
            namespace, _, template = template.partition(":")
        else:
            namespace = None

        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_TEMPLATE).template_load(template)

    def template_exists(self, template: str) -> bool:
        if ":" in template:
            namespace, _, template = template.partition(":")
        else:
            namespace = None

        return NAMESPACES.get(namespace, NAMESPACE_DEFAULT_TEMPLATE).template_exists(template)

    def file_exists(self, file: str) -> bool:
        return NAMESPACE_DEFAULT_FILE.file_exists(file)

    def file_get_link(self, url: str) -> str:
        return NAMESPACE_DEFAULT_FILE.file_get_link(url)

    def file_get_img(self, url: str, thumb: Optional[int]) -> str:
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
