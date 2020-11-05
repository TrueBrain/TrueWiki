import wikitextparser

from wikitexthtml.render import wikilink

from ...wiki_page import WikiPage


def add_footer(instance: WikiPage, page: str):
    if not instance.categories:
        return ""

    categories_content = set()
    for category in instance.categories:
        label = category.split("/")[-1]
        categories_content.add(f"<li>[[:Category:{category}|{label}]]</li>")

    wtp = wikitextparser.parse("\n".join(sorted(categories_content)))
    wikilink.replace(WikiPage(page), wtp)
    return '<div id="categories"><div>Categories:</div><ul>' + wtp.string + "</ul></div>"
