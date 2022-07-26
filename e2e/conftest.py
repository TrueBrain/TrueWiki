import asyncio
import ctypes
import os
import pytest
import shutil
import signal

from ctypes.util import find_library
from tempfile import TemporaryDirectory
from playwright.sync_api import Page


temp_folder = None
python_proc = None


async def set_death_signal():
    PR_SET_PDEATHSIG = 1

    libc = ctypes.CDLL(find_library("c"))
    libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0)


async def _run_server():
    global temp_folder, python_proc

    # Make sure we can find our way to the code in the temporary folder.
    cwd = os.getcwd()
    os.environ["PYTHONPATH"] = cwd
    os.environ["PYTHONUNBUFFERED"] = "1"

    # Create a temporary folder, so multiple runs don't influence each other.
    temp_folder = TemporaryDirectory(prefix="truewiki")
    folder = temp_folder.name
    os.chdir(folder)

    # Copy the required folders to the temporary folder.
    shutil.copytree(f"{cwd}/static", "static")
    shutil.copytree(f"{cwd}/templates", "templates")
    # Make sure some mandatory files exist.
    os.makedirs("data")
    with open("data/LICENSE.mediawiki", "w") as f:
        f.write("end-to-end test file")

    # Run TrueWiki, with coverage enabled.
    command = ["coverage", "run", "--branch", "--source", "truewiki"]
    command.extend(
        [
            "-m",
            "truewiki",
            "--port",
            "8080",
            "--storage",
            "local",
            "--user",
            "developer",
            "--frontend-url",
            "http://localhost:8080/",
            "--cache-page-folder",
            "cache/",
        ]
    )
    python_proc = await asyncio.create_subprocess_exec(
        command[0],
        *command[1:],
        stdout=asyncio.subprocess.PIPE,
        preexec_fn=set_death_signal,
    )
    # Make sure we switch back to the project folder.
    os.chdir(cwd)

    # Wait for the startup line to be shown.
    await python_proc.stdout.readline()


@pytest.fixture(scope="session", autouse=True)
def run_server():
    # Create a new event loop for our server.
    loop = asyncio.new_event_loop()

    # Start the server.
    loop.run_until_complete(_run_server())

    # Give control back to PyTest.
    yield

    # Terminate the application and temporary folder.
    python_proc.terminate()
    loop.run_until_complete(python_proc.wait())
    temp_folder.cleanup()


@pytest.fixture(autouse=True)
def timeout(page: Page):
    page.set_default_timeout(1000)
    page.set_default_navigation_timeout(1000)


@pytest.fixture
def login(page: Page):
    page.goto("http://localhost:8080/user/login")

    # We run the test in developer-mode, as we lack credentials for SSOs.
    page.locator("text=Login as developer").click()
    page.locator("[name=username]").fill("test")
    page.locator("[type=submit]").click()
