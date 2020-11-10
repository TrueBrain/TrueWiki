import html
import urllib

from wikitexthtml.exceptions import InvalidWikiLink

from ..wiki_page import WikiPage


def create(page):
    if not page:
        return '<li class="crumb"><a href="/">OpenTTD\'s Wiki</a></li>'

    spage = page.split("/")

    breadcrumbs = []

    if spage[0] in ("Category", "File", "Folder", "Template"):
        language_index = 1
        if spage[0] == "Folder":
            language_index = 2

        if len(spage) > language_index and spage[language_index] != "Main Page":
            language = spage[language_index]
            breadcrumbs.append(f'<li class="crumb"><a href="/{language}/">OpenTTD\'s Wiki</a></li>')
        else:
            breadcrumbs.append('<li class="crumb"><a href="/">OpenTTD\'s Wiki</a></li>')

    breadcrumb = "/"
    for i, p in enumerate(spage):
        if p == "Main Page" or not p:
            continue

        if i == len(spage) - 1:
            breadcrumb += f"{p}"
        else:
            breadcrumb += f"{p}/"

        title = breadcrumb[1:]
        if title.endswith("/"):
            title += "Main Page"

        try:
            title = WikiPage(breadcrumb[1:]).clean_title(title)
        except InvalidWikiLink:
            break

        title = html.escape(title)
        href = urllib.parse.quote(breadcrumb)

        breadcrumbs.append(f'<li class="crumb"><a href="{href}">{title}</a></li>')

    if not breadcrumbs:
        breadcrumbs.append('<li class="crumb"><a href="/">OpenTTD\'s Wiki</a></li>')
    else:
        breadcrumbs[-1] = breadcrumbs[-1].replace('<li class="crumb">', '<li class="crumb selected">')

    return "\n".join(breadcrumbs)
