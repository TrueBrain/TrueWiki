import click
import glob
import os

from openttd_helpers import click_helper
from typing import List

STORAGE_FOLDER = None


class Storage:
    def __init__(self) -> None:
        self._folder = STORAGE_FOLDER

    def prepare(self):
        pass

    def reload(self):
        pass

    def commit(self, user, commit_message):
        pass

    def get_history_url(self, page):
        return ""

    def get_repository_url(self):
        return ""

    def file_exists(self, filename: str) -> bool:
        return os.path.exists(f"{self._folder}/{filename}")

    def file_getsize(self, filename: str) -> int:
        return os.path.getsize(f"{self._folder}/{filename}")

    def file_read(self, filename: str) -> str:
        with open(f"{self._folder}/{filename}") as fp:
            return fp.read()

    def file_write(self, filename: str, content, mode="w") -> None:
        with open(f"{self._folder}/{filename}", mode) as fp:
            fp.write(content)

    def file_remove(self, filename: str) -> None:
        os.unlink(f"{self._folder}/{filename}")

    def file_rename(self, old_filename: str, new_filename: str) -> None:
        os.rename(f"{self._folder}/{old_filename}", f"{self._folder}/{new_filename}")

    def dir_exists(self, dirname: str) -> bool:
        return os.path.isdir(f"{self._folder}/{dirname}")

    def dir_make(self, dirname: str) -> None:
        os.makedirs(f"{self._folder}/{dirname}", exist_ok=True)

    def dir_listing(self, dirname: str) -> List[str]:
        return [item[len(f"{self._folder}/") :] for item in glob.glob(f"{self._folder}/{dirname}/*")]

    @property
    def folder(self):
        return self._folder


@click_helper.extend
@click.option(
    "--storage-folder",
    help="Folder to use for storage.",
    type=click.Path(dir_okay=True, file_okay=False),
    default="./data",
    show_default=True,
)
def click_storage_local(storage_folder):
    global STORAGE_FOLDER

    STORAGE_FOLDER = storage_folder.rstrip("/")
