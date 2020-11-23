import wikitextparser

from wikitexthtml.render import (
    preprocess,
    parameter,
    parser_function,
)

from . import (
    config,
    singleton,
)
from .views import sitemap
from .wiki_page import WikiPage


def wrap_page(page, wrapper, variables, templates):
    with open(f"templates/{wrapper}.mediawiki", "r") as fp:
        body = fp.read()

    wiki_page = WikiPage(page)
    body = preprocess.begin(wiki_page, body)
    wtp = wikitextparser.parse(body)

    if wrapper != "Error":
        if wiki_page.has_history(page):
            filename = wiki_page.page_ondisk_name(page)
            if filename:
                variables["history_url"] = singleton.STORAGE.get_history_url(filename)
        variables["has_source"] = "1" if wiki_page.has_source(page) else ""
        variables["does_exist"] = "1" if wiki_page.has_history(page) else ""
        variables["create_page_name"] = wiki_page.get_create_page_name(page)
        variables["repository_url"] = singleton.STORAGE.get_repository_url()

    variables["language"] = wiki_page.page_get_language(page) or ""
    variables["has_search"] = "1" if sitemap.FRONTEND_URL else ""

    variables["css"] = config.HTML_SNIPPETS["css"]
    variables["favicon"] = config.FAVICON
    variables["html_footer"] = config.HTML_SNIPPETS["footer"]
    variables["html_header"] = config.HTML_SNIPPETS["header"]
    variables["javascript"] = config.HTML_SNIPPETS["javascript"]
    variables["license"] = config.LICENSE
    variables["project_name"] = config.PROJECT_NAME

    arguments = [wikitextparser.Argument(f"|{name}={value}") for name, value in variables.items()]
    parameter.replace(wiki_page, wtp, arguments)

    parser_function.replace(wiki_page, wtp)
    for template in reversed(wtp.templates):
        name = template.name.strip()
        if name in templates:
            template.string = templates[name]

    return wtp.string
