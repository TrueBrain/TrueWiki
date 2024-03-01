from playwright.sync_api import Page, expect


def test_preview_page(page: Page, login):
    """Edit a page, and check preview. Make sure original content is unchanged."""
    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("http://localhost:8080/edit/en/Main%20Page")

    expect(page.locator("text=My Third Edit")).to_be_visible()

    page.locator("[name=content]").fill("My Preview Edit")
    with page.expect_navigation():
        page.locator("[name=preview]").click()
    page.wait_for_url("http://localhost:8080/edit/en/Main%20Page")

    expect(page.locator("text=This is a preview. Changes have not yet been saved.")).to_be_visible()
    expect(page.locator('p:has-text("My Preview Edit")')).to_be_visible()
    expect(page.locator('textarea:has-text("My Preview Edit")')).to_be_visible()

    # Make sure the actual page isn't changed.
    page.goto("http://localhost:8080/en/Main%20Page")
    expect(page.locator("text=My Third Edit")).to_be_visible()


def test_preview_invalid_slash(page: Page, login):
    """You cannot name a page ending with a slash."""
    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/en/Main%20Page")

    page.locator("[name=page]").fill("en/Main Page/")
    with page.expect_navigation():
        page.locator("[name=preview]").click()
    page.wait_for_url("http://localhost:8080/edit/en/Main%20Page")

    expect(page.locator('text=Page name "en/Main Page/" cannot end with a "/".')).to_be_visible()
