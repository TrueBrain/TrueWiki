from playwright.sync_api import Page, expect


def test_folder_main_page(page: Page):
    """Check if the folder of the main page is listing the right pages."""
    page.goto("http://localhost:8080/")

    folder = page.locator("#folder >> text=en")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("http://localhost:8080/Folder/Page/en/")

    expect(page.locator("text=All the pages and folders inside this folder.")).to_be_visible()
    expect(page.locator('main >> a:has-text("Main Page2")')).to_be_visible()
    expect(page.locator('main >> a:has-text("Unnamed\'s Wiki")')).to_be_visible()

    # Postfixing with "Main Page" should give the exact same page.
    page.goto("http://localhost:8080/Folder/Page/en/Main%20Page")
    expect(page.locator("text=All the pages and folders inside this folder.")).to_be_visible()
    expect(page.locator('main >> a:has-text("Main Page2")')).to_be_visible()
    expect(page.locator('main >> a:has-text("Unnamed\'s Wiki")')).to_be_visible()


def test_folder_namespace(page: Page):
    """Check if the folder of the namespace is listing the right pages."""
    page.goto("http://localhost:8080/Folder/Page/en/")

    folder = page.locator("nav >> text=Page")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("http://localhost:8080/Folder/Page/")

    expect(page.locator("text=A list of all the languages within this namespace.")).to_be_visible()
    expect(page.locator('main >> a:has-text("en")')).to_be_visible()


def test_folder_root(page: Page):
    """Check if the folder of the root is listing the right pages."""
    page.goto("http://localhost:8080/Folder/Page/en/")

    folder = page.locator("nav >> text=Folder")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("http://localhost:8080/Folder/")

    expect(page.locator("text=A list of all namespaces with files and folders.")).to_be_visible()
    expect(page.locator('main >> a:has-text("Page")')).to_be_visible()
    expect(page.locator('main >> a:has-text("License")')).to_be_visible()


def test_folder_file(page: Page):
    """Check if the folder of the File namespace is listing the right pages."""
    page.goto("http://localhost:8080/Folder/File/en/")

    expect(page.locator("text=All the pages and folders inside this folder.")).to_be_visible()
    expect(page.locator("text=test.png")).to_be_visible()


def test_folder_invalid_file_in_namespace(page: Page):
    """Opening a file in a namespace has no meaning."""
    page.goto("http://localhost:8080/Folder/Page/test")

    expect(page.locator("text=You cannot view files in the Folder namespace.")).to_be_visible()


def test_folder_invalid_language(page: Page):
    """Opening a folder in a language that doesn't exist."""
    page.goto("http://localhost:8080/Folder/Page/zz/")

    expect(
        page.locator('text=Page name "Folder/Page/zz/Main Page" is in language "zz" that does not exist.')
    ).to_be_visible()


def test_folder_invalid_namespace(page: Page):
    """Opening a folder in a namespace that doesn't exist."""
    page.goto("http://localhost:8080/Folder/Page2/")

    expect(
        page.locator('text=Page name "Folder/Page2/Main Page" is in namespace "Page2" that does not exist.')
    ).to_be_visible()
