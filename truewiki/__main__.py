import logging

from aiohttp import web
from aiohttp.web_log import AccessLogger
from openttd_helpers import click_helper
from openttd_helpers.logging_helper import click_logging
from openttd_helpers.sentry_helper import click_sentry

from .metadata import load_metadata
from .web_routes import routes
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
def main():
    print("Loading metadata ...")
    load_metadata()

    print("Starting webserver ...")
    webapp = web.Application()
    webapp.router.add_static("/uploads", "data/File/")
    webapp.router.add_static("/static", "static/")
    webapp.add_routes(routes)

    web.run_app(webapp, host="127.0.0.1", port=8000, access_log_class=ErrorOnlyAccessLogger)


if __name__ == "__main__":
    main()
