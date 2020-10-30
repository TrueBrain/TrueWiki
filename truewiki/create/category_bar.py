import wikitextparser

from wikitexthtml.render import wikilink

from ..wiki_page import WikiPage


def create(page, categories):
    categories_content = set()
    for category in categories:
        label = "/".join(category.split("/")[1:])
        categories_content.add(f"<li>[[:Category:{category}|{label}]]</li>")

    wtp = wikitextparser.parse("\n".join(sorted(categories_content)))
    wikilink.replace(WikiPage(page), wtp)
    return '<div id="categories"><div>Categories:</div><ul>' + wtp.string + "</ul></div>"
