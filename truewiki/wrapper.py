import wikitextparser

from wikitexthtml.render import (
    preprocess,
    parameter,
    parser_function,
)

from . import singleton
from .wiki_page import WikiPage


def wrap_page(page, wrapper, variables, templates):
    with open(f"templates/{wrapper}.mediawiki", "r") as fp:
        body = fp.read()

    wiki_page = WikiPage(page)
    body = preprocess.begin(wiki_page, body)
    wtp = wikitextparser.parse(body)

    if wiki_page.has_history(page):
        filename = wiki_page.page_ondisk_name(page)
        if filename:
            variables["history_url"] = singleton.STORAGE.get_history_url(filename)
    variables["has_source"] = "1" if wiki_page.has_source(page) else ""

    arguments = [wikitextparser.Argument(f"|{name}={value}") for name, value in variables.items()]
    parameter.replace(wiki_page, wtp, arguments)

    parser_function.replace(wiki_page, wtp)
    for template in reversed(wtp.templates):
        name = template.name.strip()
        if name in templates:
            template.string = templates[name]

    return wtp.string
