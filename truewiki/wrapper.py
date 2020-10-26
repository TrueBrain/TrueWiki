import wikitextparser

from wikitexthtml.render import (
    preprocess,
    parameter,
    parser_function,
)

from .wiki_page import WikiPage


def wrap_page(page, wrapper, variables):
    with open(f"templates/{wrapper}.mediawiki", "r") as fp:
        body = fp.read()

    wiki_page = WikiPage(page)
    body = preprocess.begin(wiki_page, body)
    wtp = wikitextparser.parse(body)

    parameter.replace(wiki_page, wtp, [])
    for template in reversed(wtp.templates):
        name = template.name.strip()
        if name in variables:
            template.string = variables[name]
    parser_function.replace(wiki_page, wtp)

    return wtp.string
