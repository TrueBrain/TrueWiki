import click

from openttd_helpers import click_helper

_folder = None


class Storage:
    def __init__(self) -> None:
        self._folder = _folder

    def reload(self):
        pass

    @property
    def folder(self):
        return self._folder


@click_helper.extend
@click.option(
    "--storage-folder",
    help="Folder to use for storage.",
    type=click.Path(dir_okay=True, file_okay=False),
    default="data",
    show_default=True,
)
def click_local_storage(storage_folder):
    global _folder

    _folder = storage_folder.rstrip("/")
