from .. import (
    metadata,
    wiki_page,
)


class Namespace:
    namespace = ""

    @staticmethod
    def page_load(page: str) -> str:
        raise NotImplementedError

    @staticmethod
    def page_exists(page: str) -> bool:
        raise NotImplementedError

    @staticmethod
    def page_is_valid(page: str) -> bool:
        return False

    @staticmethod
    def has_source(page: str) -> bool:
        return False

    @classmethod
    def has_history(cls, page: str) -> bool:
        return cls.has_source(page) and cls.page_exists(page)

    @staticmethod
    def add_language(instance: wiki_page.WikiPage, page: str) -> str:
        return ""

    @staticmethod
    def add_content(instance: wiki_page.WikiPage, page: str) -> str:
        return ""

    @staticmethod
    def add_footer(instance: wiki_page.WikiPage, page: str) -> str:
        return ""

    @classmethod
    def clean_title(cls, page: str, title: str, root_name: str = None) -> str:
        spage = page.split("/")
        stitle = title.split("/")

        postfix = ""

        # Find the language indicator for the page.
        if spage[0] == "Folder":
            language_page = spage[2] if len(spage) > 3 else ""
        elif spage[0] in ("Category", "File", "Template"):
            language_page = spage[1] if len(spage) > 2 else ""
        else:
            language_page = spage[0]

        # Find the language indicator for the title.
        if stitle[0] == "Folder":
            language_title = stitle[2] if len(stitle) > 3 else ""
        elif stitle[0] in ("Category", "File", "Template"):
            language_title = stitle[1] if len(stitle) > 2 else ""
        else:
            language_title = stitle[0]

        # If the language of the page differs from the title, indicate to the
        # user he will change language when clicking the link.
        if language_page and language_title and language_page != language_title:
            postfix = f" ({language_title})"

        if stitle[-1] != "Main Page":
            return stitle[-1] + postfix

        if len(stitle) > 2:
            return stitle[-2] + postfix

        if root_name:
            return root_name + postfix
        return cls.namespace + postfix

    @staticmethod
    def page_ondisk_name(page: str) -> str:
        return f"{page}.mediawiki"

    @staticmethod
    def get_used_on_pages(page: str) -> list:
        return metadata.TEMPLATES[page]

    @staticmethod
    def page_get_correct_case(page: str) -> str:
        return metadata.PAGES_LC.get(page.lower(), page)

    @staticmethod
    def get_create_page_name(page: str) -> str:
        return ""

    @classmethod
    def template_load(cls, template: str) -> str:
        return f'<a href="/{cls.namespace}/{template}" title="{template}">{cls.namespace}/{template}</a>'

    @staticmethod
    def template_exists(template: str) -> bool:
        return False
