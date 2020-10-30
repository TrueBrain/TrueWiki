from ..wiki_page import WikiPage


def create(page):
    spage = page.split("/")

    breadcrumbs = []

    if spage[0] in ("Category", "Folder", "Template"):
        if len(spage) > 1 and spage[1] != "Main Page":
            language = spage[1]
            breadcrumbs.append(f'<li class="crumb"><a href="/{language}/">OpenTTD\'s Wiki</a></li>')
        else:
            breadcrumbs.append('<li class="crumb"><a href="/">OpenTTD\'s Wiki</a></li>')

    breadcrumb = "/"
    for i, p in enumerate(spage):
        if p == "Main Page":
            continue

        if i == len(spage) - 1:
            breadcrumb += f"{p}"
        else:
            breadcrumb += f"{p}/"

        title = breadcrumb[1:]
        if title.endswith("/"):
            title += "Main Page"
        title = WikiPage(breadcrumb).clean_title(title)

        breadcrumbs.append(f'<li class="crumb"><a href="{breadcrumb}">{title}</a></li>')
    breadcrumbs[-1] = breadcrumbs[-1].replace('<li class="crumb">', '<li class="crumb selected">')
    return "\n".join(breadcrumbs)
