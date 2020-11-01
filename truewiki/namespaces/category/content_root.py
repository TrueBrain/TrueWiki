from ..folder import content as folder_content


def add_content(page: str) -> str:
    # List all the languages in the Category folder.
    return folder_content.add_content("Folder/Category/Main Page", namespace="Category")
