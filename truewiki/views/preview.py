from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def view(user, page: str, body: str) -> str:
    if page.endswith("/"):
        page += "Main Page"

    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return None

    wtp = wiki_page.prepare(body)
    content = wiki_page.render_page(wtp)
    errors = [f"<li>{error}</li>" for error in wiki_page.errors]

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

    templates["language"] = wiki_page.add_language(page)
    templates["footer"] = wiki_page.add_footer(page)
    templates["content"] += wiki_page.add_content(page)
    return wrap_page(page, "Preview", variables, templates)
