from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def view(user, page: str, body: str) -> str:
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
