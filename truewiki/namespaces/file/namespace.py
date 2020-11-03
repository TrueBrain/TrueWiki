import logging

from .. import base
from ... import wiki_page

log = logging.getLogger(__name__)


class Namespace(base.Namespace):
    namespace = "File"
    force_link = ":File:"

    @staticmethod
    def page_load(page: str) -> str:
        # TODO -- Implement
        return ""

    @staticmethod
    def page_exists(page: str) -> bool:
        # TODO -- Implement
        return False


wiki_page.register_namespace(Namespace)
