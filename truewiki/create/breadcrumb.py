from ..wiki_page import WikiPage


def create(page):
    spage = page.split("/")

    breadcrumbs = []

    if spage[0] in ("Category", "Folder", "Templates"):
        if len(spage) > 1:
            language = spage[1]
            breadcrumbs.append(f'<li class="crumb"><a href="/{language}/">OpenTTD\'s Wiki</a></li>')
        else:
            breadcrumbs.append('<li class="crumb"><a href="/">OpenTTD\'s Wiki</a></li>')

    is_folder = spage[0] == "Folder"

    breadcrumb = "" if is_folder else "/"
    for i, p in enumerate(spage):
        if p == "Main Page":
            continue

        if is_folder:
            breadcrumb += f"/{p}"
        elif i == len(spage) - 1:
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
