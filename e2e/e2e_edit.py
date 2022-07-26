from playwright.sync_api import Page, expect


def test_edit_page_without_login(page: Page):
    """If we are not logged in, we should be redirected to the login page."""
    page.goto("http://localhost:8080/edit/en/Main%20Page")
    page.wait_for_url("/user/login?location=edit/en/Main%20Page")


def test_create_page(page: Page, login):
    """When we first start, there are no pages yet. This creates the main page."""
    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()

    page.locator("[name=content]").fill("My First Edit")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/en/Main%20Page")

    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator("text=My First Edit")).to_be_visible()


def test_edit_page(page: Page, login):
    """Check if we can actually edit the page."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=content]").fill("My Second Edit")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/en/Main%20Page")

    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator("text=My Second Edit")).to_be_visible()


def test_rename_page(page: Page, login):
    """Check if we can rename the main page to something else."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=page]").fill("en/Main Page2")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/en/Main%20Page2")

    expect(page.locator('a:has-text("Main Page2")')).to_be_visible()


def test_create_page_again(page: Page, login):
    """Now we have renamed the page, we should be able to create the main page again."""
    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()

    page.locator("[name=content]").fill("My Third Edit")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/en/Main%20Page")

    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator("text=My Third Edit")).to_be_visible()


def test_rename_page_again(page: Page, login):
    """Trying to rename it to Main Page2 again should return an error."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=page]").fill("en/Main Page2")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/en/Main%20Page")

    expect(page.locator('text=Page name "en/Main Page2" already exists')).to_be_visible()


def test_rename_page_invalid_slash(page: Page, login):
    """You cannot name a page ending with a slash."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=page]").fill("en/Main Page/")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/en/Main%20Page")

    expect(page.locator('text=Page name "en/Main Page/" cannot end with a "/".')).to_be_visible()


def test_rename_page_invalid_name(page: Page, login):
    """Page name needs to be in a language."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=page]").fill("Main Page")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/en/Main%20Page")

    expect(page.locator('text=Page name "./Main Page" contains a filename/folder that starts with a dot, which is not allowed.')).to_be_visible()


def test_rename_page_invalid_language(page: Page, login):
    """Page name needs to be in a valid language."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=page]").fill("de/Main Page")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/en/Main%20Page")

    expect(page.locator('text=Page name "de/Main Page" is in language "de" that does not exist.')).to_be_visible()


def test_rename_page_invalid_casing(page: Page, login):
    """Page name cannot be the same to a similar page with different casing."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=page]").fill("en/main page2")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/en/Main%20Page")

    expect(page.locator('text=Page name "en/main page2" conflicts with "en/Main Page2", which already exists.')).to_be_visible()


def test_edit_page_missing_language(page: Page, login):
    """Editing a page with the language missing."""
    page.goto("http://localhost:8080/edit/main%20page2")
    expect(page.locator('text=Page name "main page2" is missing either a language or a namespace')).to_be_visible()


def test_edit_page_different_casing(page: Page, login):
    """Editing a page with different casing is not allowed."""
    page.goto("http://localhost:8080/edit/en/main%20page2")
    expect(page.locator('text=Page name "en/main page2" conflicts with "en/Main Page2". Did you mean to edit Main Page2?')).to_be_visible()
