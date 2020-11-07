from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def view(user, page: str) -> str:
    if page.endswith("/"):
        page += "Main Page"

    wiki_page = WikiPage(page)
    if not wiki_page.page_is_valid(page):
        return 404, None

    templates = {
        "content": wiki_page.render().html,
        "breadcrumbs": breadcrumb.create(page),
    }
    variables = {
        "display_name": user.display_name if user else "",
        "errors": len(wiki_page.errors) if wiki_page.errors else "",
    }

    templates["language"] = wiki_page.add_language(page)
    templates["footer"] = wiki_page.add_footer(page)
    templates["content"] += wiki_page.add_content(page)

    if wiki_page.page_exists(page):
        status_code = 200
    else:
        status_code = 404

    return status_code, wrap_page(page, "Page", variables, templates)
