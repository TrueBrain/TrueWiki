from ..content import breadcrumb
from ..wiki_page import WikiPage
from ..wrapper import wrap_page


def view(user, page: str) -> str:
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
