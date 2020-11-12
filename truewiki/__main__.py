import asyncio
import click
import logging

from aiohttp import web
from aiohttp.web_log import AccessLogger
from openttd_helpers import click_helper
from openttd_helpers.logging_helper import click_logging
from openttd_helpers.sentry_helper import click_sentry

from . import (
    singleton,
    validate,
)
from .metadata import click_metadata
from .storage.git import click_storage_git
from .storage.github import click_storage_github
from .storage.local import click_storage_local
from .user.github import click_user_github
from .user_session import (
    click_user_session,
    register_webroutes,
)
from .web_routes import (
    click_web_routes,
    routes,
)

from .namespaces import (  # noqa
    category,
    file,
    folder,
    page,
    template,
    translation,
)


log = logging.getLogger(__name__)

# Don't allow any file above 4 MiB.
MAX_UPLOAD_SIZE = (1024 ** 2) * 4


class ErrorOnlyAccessLogger(AccessLogger):
    def log(self, request, response, time):
        # Only log if the status was not successful
        if not (200 <= response.status < 400):
            super().log(request, response, time)


async def wait_for_storage():
    await singleton.STORAGE.wait_for_ready()


@click_helper.command()
@click_logging  # Should always be on top, as it initializes the logging
@click_sentry
@click.option(
    "--bind", help="The IP to bind the server to", multiple=True, default=["::1", "127.0.0.1"], show_default=True
)
@click.option("--port", help="Port of the web server", default=80, show_default=True)
@click.option(
    "--storage",
    type=click.Choice(["github", "git", "local"], case_sensitive=False),
    required=True,
    callback=click_helper.import_module("truewiki.storage", "Storage"),
)
@click_web_routes
@click_metadata
@click_storage_local
@click_storage_git
@click_storage_github
@click_user_session
@click_user_github
@click.option("--validate-all", help="Validate all mediawiki files and report all errors", is_flag=True)
def main(bind, port, storage, validate_all):
    log.info("Reload storage ..")
    instance = storage()
    singleton.STORAGE = instance

    instance.prepare()
    instance.reload()

    # At startup, ensure storage is loaded in.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(wait_for_storage())

    if validate_all:
        validate.all()
        return

    webapp = web.Application(client_max_size=MAX_UPLOAD_SIZE)
    webapp.router.add_static("/uploads", f"{instance.folder}/File/")
    webapp.router.add_static("/static", "static/")
    register_webroutes(webapp)
    webapp.add_routes(routes)

    web.run_app(webapp, host=bind, port=port, access_log_class=ErrorOnlyAccessLogger)


if __name__ == "__main__":
    main(auto_envvar_prefix="TRUEWIKI")
