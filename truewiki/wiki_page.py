import os

from wikitexthtml import Page

SPECIAL_FOLDERS = ("Template/", "Category/")


class WikiPage(Page):
    def __init__(self, page: str) -> None:
        super().__init__(page)
        self.en_page = None
        self.categories = []

    def page_load(self, page: str) -> str:
        for special_folder in SPECIAL_FOLDERS:
            if page.startswith(special_folder):
                prefix = special_folder[:-1]
                page = page[len(special_folder) :]
                break
        else:
            prefix = "Page"

        with open(f"data/{prefix}/{page}.mediawiki") as fp:
            body = fp.read()
        return body

    def page_exists(self, page: str) -> bool:
        for special_folder in SPECIAL_FOLDERS:
            if page.startswith(special_folder):
                prefix = special_folder[:-1]
                page = page[len(special_folder) :]
                break
        else:
            prefix = "Page"

        return os.path.exists(f"data/{prefix}/{page}.mediawiki")

    def template_load(self, template: str) -> str:
        with open(f"data/Template/{template}.mediawiki") as fp:
            return fp.read()

    def template_exists(self, template: str) -> bool:
        return os.path.exists(f"data/Template/{template}.mediawiki")

    def file_exists(self, file: str) -> bool:
        return os.path.exists(f"data/File/{file}")

    def clean_url(self, url: str) -> str:
        if url.endswith("Main Page"):
            return url[: -len("Main Page")]
        return url

    def clean_title(self, title: str) -> str:
        stitle = title.split("/")
        if title.endswith("Main Page"):
            if len(stitle) > 2:
                return stitle[-2]
            else:
                return "OpenTTD's Wiki"
        else:
            return stitle[-1]
