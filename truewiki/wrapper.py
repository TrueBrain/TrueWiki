import wikitextparser

from wikitexthtml.render import (
    preprocess,
    parameter,
    parser_function,
)

from . import web_routes
from .wiki_page import WikiPage


def wrap_page(page, wrapper, variables, templates):
    with open(f"templates/{wrapper}.mediawiki", "r") as fp:
        body = fp.read()

    wiki_page = WikiPage(page)
    body = preprocess.begin(wiki_page, body)
    wtp = wikitextparser.parse(body)

    arguments = [wikitextparser.Argument(f"|{name}={value}") for name, value in variables.items()]
    parameter.replace(wiki_page, wtp, arguments)

    spage = page.split("/")
    breadcrumbs = []
    breadcrumb = "/"
    for i, p in enumerate(spage):
        if p == "Main Page":
            continue

        if i == len(spage) - 1:
            breadcrumb += f"{p}"
        else:
            breadcrumb += f"{p}/"

        if i == 0:
            p = "OpenTTD's Wiki"

        breadcrumbs.append(f'<li class="crumb"><a href="{breadcrumb}">{p}</a></li>')
    breadcrumbs[-1] = breadcrumbs[-1].replace('<li class="crumb">', '<li class="crumb selected">')

    templates["HISTORY_URL"] = web_routes.STORAGE.get_history_url(wiki_page.page_ondisk_name(page))
    templates["breadcrumbs"] = "\n".join(breadcrumbs)

    for template in reversed(wtp.templates):
        name = template.name.strip()
        if name in templates:
            template.string = templates[name]
    parser_function.replace(wiki_page, wtp)

    return wtp.string
