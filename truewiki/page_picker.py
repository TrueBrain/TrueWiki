import html

from . import metadata

NAMESPACES = ("Page", "Template", "Category", "File")


def split(page: str) -> tuple:
    """Split a page name into its namespace, language and name."""
    parts = page.split("/")
    namespace = "Page"
    if parts[0] in NAMESPACES[1:]:
        namespace = parts.pop(0)

    language = parts[0] if parts else ""
    name = "/".join(parts[1:])
    return namespace, language, name


def join(namespace: str, language: str, name: str) -> str:
    """Join a namespace, language and name into a page name."""
    if namespace not in NAMESPACES[1:]:
        return f"{language}/{name}"
    return f"{namespace}/{language}/{name}"


def _options(values, selected: str) -> str:
    options = []
    for value in values:
        value = html.escape(value)
        attribute = ' selected="selected"' if value == selected else ""
        options.append(f'<option value="{value}"{attribute}>{value}</option>')
    return "".join(options)


def render(page: str, is_file: bool) -> str:
    """HTML form fields to pick the namespace, language and name of a new page."""
    namespace, language, name = split(page)
    choices = ("File",) if is_file else NAMESPACES[:3]

    languages = set(metadata.LANGUAGES)
    if language:
        languages.add(language)

    namespaces = _options(choices, namespace)
    languages = _options(sorted(languages), html.escape(language))
    name = html.escape(name)

    return (
        '<div id="page-picker">'
        '<label for="page-namespace">Type '
        f'<select id="page-namespace" name="page-namespace">{namespaces}</select>'
        "</label>"
        '<label for="page-language">Language '
        f'<select id="page-language" name="page-language">{languages}</select>'
        "</label>"
        '<label for="page-name" id="page-picker-name">'
        f'Name <input type="text" id="page-name" name="page-name" value="{name}" />'
        "</label>"
        "</div>"
    )
