import logging
import os

from typing import Optional

from .. import base
from ... import (
    singleton,
    wiki_page,
)

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
