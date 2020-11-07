import click

from openttd_helpers import click_helper

STORAGE_FOLDER = None


class Storage:
    def __init__(self) -> None:
        self._folder = STORAGE_FOLDER

    def prepare(self):
        pass

    def reload(self):
        pass

    def get_history_url(self, page):
        return ""

    def get_repository_url(self):
        return ""

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
