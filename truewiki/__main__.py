import asyncio
import click
import logging
import os

from aiohttp import web
from aiohttp.web_log import AccessLogger
from openttd_helpers import click_helper
from openttd_helpers.logging_helper import click_logging
from openttd_helpers.sentry_helper import click_sentry

from . import (
    config,
    singleton,
    validate,
)
from .metadata import click_metadata
from .storage.git import click_storage_git
from .storage.github import click_storage_github
from .storage.gitlab import click_storage_gitlab
from .storage.local import click_storage_local
from .user.github import click_user_github
from .user.gitlab import click_user_gitlab
from .user.microsoft import click_user_microsoft
from .user_session import (
    click_user_session,
    get_user_by_bearer,
    register_webroutes,
    remove_session_cookie,
    SESSION_COOKIE_NAME,
)
from .views.page import click_page
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
MAX_UPLOAD_SIZE = (1024**2) * 4
# Cache static files for 24 hours.
CACHE_TIME_STATIC = 3600 * 24
# Cache uploads for 5 minutes by default. These files can be overwritten by
# users, so high cache times can be frustrating to the user.
CACHE_TIME_UPLOADS = 300


class ErrorOnlyAccessLogger(AccessLogger):
    def log(self, request, response, time):
        # Only log if the status was not successful
        if not (200 <= response.status < 400):
            super().log(request, response, time)


@web.middleware
async def remove_cookie_middleware(request, handler):
    response = await handler(request)

    # Does the user have a cookie?
    if SESSION_COOKIE_NAME not in request.cookies:
        return response

    # But doesn't it result in a user?
    if get_user_by_bearer(request.cookies.get(SESSION_COOKIE_NAME)):
        return response

    # Remove the cookie.
    remove_session_cookie(response)
    return response


async def cache_on_prepare(request, response, cache_time_uploads):
    if request.path.startswith("/static"):
        # Cache everything in the /static folder for a day.
        response.headers["Cache-Control"] = f"public, max-age={CACHE_TIME_STATIC}"

    if request.path.startswith("/uploads"):
        # Cache uploaded files.
        response.headers["Cache-Control"] = f"public, max-age={cache_time_uploads}"


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
    type=click.Choice(["github", "gitlab", "git", "local"], case_sensitive=False),
    required=True,
    callback=click_helper.import_module("truewiki.storage", "Storage"),
)
@click.option(
    "--frontend-url",
    help="URL of the frontend, used for creating absolute links in the sitemap.xml",
)
@click.option(
    "--cache-time", help="Cache time of uploaded images (in seconds)", default=CACHE_TIME_UPLOADS, show_default=True
)
@click_web_routes
@click_metadata
@click_storage_local
@click_storage_git
@click_storage_github
@click_storage_gitlab
@click_user_session
@click_user_github
@click_user_gitlab
@click_user_microsoft
@click_page
@click.option("--validate-all", help="Validate all mediawiki files and report all errors", is_flag=True)
def main(bind, port, storage, frontend_url, cache_time, validate_all):
    if frontend_url and frontend_url.endswith("/"):
        frontend_url = frontend_url[:-1]
    singleton.FRONTEND_URL = frontend_url

    log.info("Reload storage ..")
    instance = storage()
    singleton.STORAGE = instance

    instance.prepare()
    instance.reload()

    # At startup, ensure storage is loaded in.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(wait_for_storage())

    config.load()

    if validate_all:
        validate.all()
        return

    webapp = web.Application(client_max_size=MAX_UPLOAD_SIZE, middlewares=[remove_cookie_middleware])
    webapp.on_response_prepare.append(lambda request, response: cache_on_prepare(request, response, cache_time))

    # Ensure these folders exists, otherwise add_static() will complain.
    os.makedirs(f"{instance.folder}/File", exist_ok=True)
    os.makedirs(f"{instance.folder}/static", exist_ok=True)

    webapp.router.add_static("/uploads", f"{instance.folder}/File/")
    webapp.router.add_static("/static/truewiki", "static/truewiki/")
    webapp.router.add_static("/static", f"{instance.folder}/static/")

    register_webroutes(webapp)
    webapp.add_routes(routes)

    web.run_app(webapp, host=bind, port=port, access_log_class=ErrorOnlyAccessLogger, loop=loop)


if __name__ == "__main__":
    main(auto_envvar_prefix="TRUEWIKI")
