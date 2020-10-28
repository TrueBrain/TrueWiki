import click
import logging
import time

from aiohttp import web
from aiohttp.web_log import AccessLogger
from openttd_helpers import click_helper
from openttd_helpers.logging_helper import click_logging
from openttd_helpers.sentry_helper import click_sentry

from . import web_routes
from .metadata import load_metadata
from .storage.github import click_storage_github
from .storage.local import click_local_storage
from .web_routes import (
    click_web_routes,
    routes,
)

from . import wikilink  # noqa


log = logging.getLogger(__name__)

SPECIAL_FOLDERS = ("Template/", "Category/")


class ErrorOnlyAccessLogger(AccessLogger):
    def log(self, request, response, time):
        # Only log if the status was not successful
        if not (200 <= response.status < 400):
            super().log(request, response, time)


@click_helper.command()
@click_logging  # Should always be on top, as it initializes the logging
@click_sentry
@click.option(
    "--bind", help="The IP to bind the server to", multiple=True, default=["::1", "127.0.0.1"], show_default=True
)
@click.option("--port", help="Port of the web server", default=80, show_default=True)
@click.option(
    "--storage",
    type=click.Choice(["github", "local"], case_sensitive=False),
    required=True,
    callback=click_helper.import_module("truewiki.storage", "Storage"),
)
@click_web_routes
@click_local_storage
@click_storage_github
def main(bind, port, storage):
    log.info("Reload storage ..")
    instance = storage()
    instance.reload()

    web_routes.STORAGE = instance

    log.info("Loading metadata (this can take a while) ...")

    start = time.time()
    load_metadata(instance.folder)
    log.info(f"Loading metadata done; took {time.time() - start:.2f} seconds")

    webapp = web.Application()
    webapp.router.add_static("/uploads", f"{instance.folder}/File/")
    webapp.router.add_static("/static", "static/")
    webapp.add_routes(routes)

    web.run_app(webapp, host=bind, port=port, access_log_class=ErrorOnlyAccessLogger)


if __name__ == "__main__":
    main()
