from ..folder import content as folder_content


def add_content(page: str) -> str:
    language = page.split("/")[1]
    print(language)

    # List all the templates in the language folder.
    return folder_content.add_content(f"Folder/Template/{language}/Main Page", namespace="Template")
