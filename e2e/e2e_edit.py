from playwright.sync_api import Page, expect


def test_create_page(page: Page, login):
    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()

    page.locator("[name=content]").fill("My First Edit")
    with page.expect_navigation():
        page.locator("[name=save]").click()

    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator("text=My First Edit")).to_be_visible()


def test_edit_page(page: Page, login):
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()

    page.locator("[name=content]").fill("My Second Edit")
    with page.expect_navigation():
        page.locator("[name=save]").click()

    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator("text=My Second Edit")).to_be_visible()
