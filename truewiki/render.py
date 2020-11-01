import wikitextparser

from wikitexthtml.render import wikilink

from . import singleton
from .content import breadcrumb
from .user_session import (
    get_user_method,
    get_user_methods,
)
from .wiki_page import WikiPage
from .wrapper import wrap_page


def render_login(user) -> str:
    login_methods = []
    for method_name in get_user_methods():
        method = get_user_method(method_name)
        login_methods.append(f'<button type="submit" name="{method_name}">{method.get_description()}</button>')

    templates = {
        "login_methods": "\n".join(login_methods),
    }
    variables = {
        "display_name": user.display_name if user else "",
    }

    return wrap_page("Login", "Login", variables, templates)


def save_edit(user, page: str, change: str) -> None:
    # TODO -- Move this function away from "render.py"
    # TODO -- Recalculate Translations and Categories
    wiki_page = WikiPage(page)

    filename = wiki_page.page_ondisk_name(page)
    with open(f"{singleton.STORAGE.folder}/{filename}", "w") as fp:
        fp.write(change)


def render_edit(user, page: str) -> str:
    wiki_page = WikiPage(page)
    body = wiki_page.page_load(page)
    wikipage = WikiPage(page).render()

    templates_used = [f"<li>[[:Template:{template}]]</li>" for template in wikipage.templates]
    errors = [f"<li>{error}</li>" for error in wikipage.errors]

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
    }

    return wrap_page(page, "Edit", variables, templates)


def render_preview(user, page: str, body: str) -> str:
    if page.endswith("/"):
        page += "Main Page"

    wikipage = WikiPage(page)
    wtp = wikipage.prepare(body)
    content = wikipage.render_page(wtp)
    errors = [f"<li>{error}</li>" for error in wikipage.errors]

    templates = {
        "content": content,
        "page": body,
        "language": "",
        "footer": "",
        "errors": "\n".join(errors),
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "display_name": user.display_name if user else "",
        "has_errors": "1" if errors else "",
    }

    templates["language"] = wikipage.add_language(page)
    templates["footer"] = wikipage.add_footer(page)
    templates["content"] += wikipage.add_content(page)
    return wrap_page(page, "Preview", variables, templates)


def render_source(user, page: str) -> str:
    body = WikiPage(page).page_load(page)
    wikipage = WikiPage(page).render()

    templates_used = [f"<li>[[:Template:{template}]]</li>" for template in wikipage.templates]
    errors = [f"<li>{error}</li>" for error in wikipage.errors]

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
    }

    return wrap_page(page, "Source", variables, templates)


def render_page(user, page: str) -> str:
    if page.endswith("/"):
        page += "Main Page"

    wikipage = WikiPage(page)

    templates = {
        "content": wikipage.render().html,
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "display_name": user.display_name if user else "",
        "errors": len(wikipage.errors) if wikipage.errors else "",
    }

    templates["language"] = wikipage.add_language(page)
    templates["footer"] = wikipage.add_footer(page)
    templates["content"] += wikipage.add_content(page)
    return wrap_page(page, "Page", variables, templates)
