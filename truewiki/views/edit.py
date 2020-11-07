import os
import wikitextparser

from wikitexthtml.render import wikilink

from .. import singleton
from ..content import breadcrumb
from ..metadata import page_changed
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def save(user, page: str, change: str) -> bool:
    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return False

    filename = wiki_page.page_ondisk_name(page)
    dirname = "/".join(filename.split("/")[:-1])

    # Make sure the folder exists.
    os.makedirs(f"{singleton.STORAGE.folder}/{dirname}", exist_ok=True)
    # Write the new source.
    with open(f"{singleton.STORAGE.folder}/{filename}", "w") as fp:
        fp.write(change)

    page_changed(filename[: -len(".mediawiki")])
    return True


def view(user, page: str) -> str:
    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return None

    filename = wiki_page.page_ondisk_name(page)
    filename = f"{singleton.STORAGE.folder}/{filename}"
    if os.path.exists(filename):
        with open(filename) as fp:
            body = fp.read()
    else:
        body = ""

    wiki_page.render()

    templates_used = [f"<li>[[:Template:{template}]]</li>" for template in wiki_page.templates]
    errors = [f"<li>{error}</li>" for error in wiki_page.errors]

    wtp = wikitextparser.parse("\n".join(sorted(templates_used)))
    wikilink.replace(WikiPage(page), wtp)
    templates_used = wtp.string

    templates = {
        "page": body,
        "templates_used": templates_used,
        "errors": "\n".join(errors),
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "has_templates_used": "1" if templates_used else "",
        "has_errors": "1" if errors else "",
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
    }

    return wrap_page(page, "Edit", variables, templates)
