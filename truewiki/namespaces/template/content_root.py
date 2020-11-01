from ..folder import content as folder_content


def add_content(page: str) -> str:
    # List all the languages in the Template folder.
    return folder_content.add_content("Folder/Template/Main Page", namespace="Template")
