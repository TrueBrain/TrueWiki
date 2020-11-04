from .. import wiki_page


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

    @staticmethod
    def has_history(page: str) -> bool:
        return Namespace.has_source(page) and Namespace.page_exists(page)

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
    def clean_title(cls, title: str) -> str:
        stitle = title.split("/")

        if stitle[-1] != "Main Page":
            return stitle[-1]

        if len(stitle) > 2:
            return stitle[-2]

        return cls.namespace

    @staticmethod
    def page_ondisk_name(page: str) -> str:
        return f"{page}.mediawiki"

    @classmethod
    def template_load(cls, template: str) -> str:
        return f'<a href="/{cls.namespace}/{template}" title="{template}">{cls.namespace}/{template}</a>'

    @staticmethod
    def template_exists(template: str) -> bool:
        return False
