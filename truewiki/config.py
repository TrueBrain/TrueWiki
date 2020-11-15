import yaml

from . import singleton

CSS = ["/static/truewiki/truewiki.css"]
FAVICON = None
HTML_SNIPPETS = {
    "css": "",
    "footer": "",
    "header": "",
    "javascript": "",
}
JAVASCRIPT = []
LICENSE = "Unlicensed"
PRIMARY_LANGUAGE = "en"
PROJECT_NAME = "Unnamed"


def load():
    global CSS, FAVICON, HTML_SNIPPETS, JAVASCRIPT, LICENSE, PRIMARY_LANGUAGE, PROJECT_NAME

    if not singleton.STORAGE.file_exists(".truewiki.yml"):
        post_load()
        return

    config = yaml.safe_load(singleton.STORAGE.file_read(".truewiki.yml"))

    CSS = config.get("css", CSS)
    FAVICON = config.get("favicon", FAVICON)
    HTML_SNIPPETS["footer"] = config.get("html-snippets", {}).get("footer", HTML_SNIPPETS["footer"])
    HTML_SNIPPETS["header"] = config.get("html-snippets", {}).get("header", HTML_SNIPPETS["header"])
    JAVASCRIPT = config.get("javascript", JAVASCRIPT)
    LICENSE = config.get("license", LICENSE)
    PRIMARY_LANGUAGE = config.get("primary-language", PRIMARY_LANGUAGE)
    PROJECT_NAME = config.get("project-name", PROJECT_NAME)

    post_load()


def post_load():
    HTML_SNIPPETS["css"] = "\n".join([f'<link rel="stylesheet" href="{css}" type="text/css" />' for css in CSS])
    HTML_SNIPPETS["javascript"] = "\n".join([f'<script src="{javascript}"></script>' for javascript in JAVASCRIPT])
