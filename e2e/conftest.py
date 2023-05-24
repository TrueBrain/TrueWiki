import asyncio
import ctypes
import os
import pytest
import shutil
import signal
import time

from ctypes.util import find_library
from tempfile import TemporaryDirectory
from playwright.sync_api import Page


temp_folder = None
python_proc = None


async def set_death_signal():
    PR_SET_PDEATHSIG = 1

    libc = ctypes.CDLL(find_library("c"))
    libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0)


async def _run_server(storage):
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
    # Make sure a few languages exist.
    os.makedirs("data/Page/en")
    with open("data/Page/en/.keep", "w") as f:
        pass
    os.makedirs("data/Page/de")
    with open("data/Page/de/.keep", "w") as f:
        pass

    # Run TrueWiki, with coverage enabled.
    command = ["coverage", "run"]
    command.extend(
        [
            "-m",
            "truewiki",
            "--port",
            "8080",
            "--storage",
            storage,
            "--user",
            "developer",
            "--frontend-url",
            "http://localhost:8080/",
            "--cache-page-folder",
            "cache/",
        ]
    )

    if storage == "github":
        branch_name = "e2e-" + str(time.time()).replace(".", "-")

        if os.getenv("TRUEWIKI_STORAGE_GITHUB_PRIVATE_KEY"):
            github_url = "git@github.com:TrueBrain/truewiki-e2e-test.git"
        else:
            github_url = "https://github.com/TrueBrain/truewiki-e2e-test"

        command.extend(
            [
                "--storage-github-url",
                github_url,
                "--storage-github-history-url",
                "https://github.com/TrueBrain/truewiki-e2e-test",
                "--storage-github-branch",
                branch_name,
            ]
        )

    if storage == "gitlab":
        branch_name = "e2e-" + str(time.time()).replace(".", "-")

        command.extend(
            [
                "--storage-gitlab-url",
                "git@gitlab.com:TrueBrain/truewiki-e2e-test.git",
                "--storage-gitlab-history-url",
                "https://gitlab.com/TrueBrain/truewiki-e2e-test",
                "--storage-gitlab-branch",
                branch_name,
            ]
        )

    python_proc = await asyncio.create_subprocess_exec(
        command[0],
        *command[1:],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        preexec_fn=set_death_signal,
    )
    # Make sure we switch back to the project folder.
    os.chdir(cwd)

    # Wait till the server reports "running".
    lines = []
    while python_proc.returncode is None and not python_proc.stdout.at_eof():
        line = await python_proc.stdout.readline()
        if line is None:
            break
        lines.append(line)

        if "Running on http://" in line.decode():
            break

    # If either the process closed or the stdout closed, the server didn't
    # actual start. And yes, it can happen stdout is already closed, but
    # the returncode isn't in yet.
    if python_proc.returncode is not None or python_proc.stdout.at_eof():
        print("Logs from TrueWiki server:")
        print((b"\n".join(lines) + await python_proc.stdout.read()).decode())
        print((b"\n".join(lines) + await python_proc.stderr.read()).decode())
        raise Exception("Failed to start TrueWiki server")

    return None


@pytest.fixture(scope="session", autouse=True)
def run_server(request):
    # Create a new event loop for our server.
    loop = asyncio.new_event_loop()

    # Start the server.
    loop.run_until_complete(_run_server(request.config.getoption("--storage")))

    # Give control back to PyTest.
    yield

    # Terminate the application and temporary folder.
    python_proc.terminate()
    loop.run_until_complete(python_proc.wait())
    temp_folder.cleanup()


def pytest_addoption(parser):
    parser.addoption("--storage", action="store", default="local", help="Storage backend")


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
