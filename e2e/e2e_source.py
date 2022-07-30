from playwright.sync_api import Page, expect


def test_source_page(page: Page):
    """Check if we can view the source page of the main page."""
    page.goto("http://localhost:8080/")

    source = page.locator("text=View Source")
    expect(source).to_be_visible()
    with page.expect_navigation():
        source.click()
    page.wait_for_url("/en/Main%20Page.mediawiki")

    expect(
        page.locator("text=You do not have permission to edit this page, because you are not logged in.")
    ).to_be_visible()
    expect(page.locator("textarea")).to_have_text("My Third Edit\n\n[[Category:en/MyPages]]")
    expect(page.locator("text=My Third Edit")).to_be_visible()


def test_source_page_non_existing(page: Page):
    """Validate we can view non-existing pages."""
    page.goto("http://localhost:8080/en/NonExistingPage.mediawiki")

    expect(
        page.locator("text=You do not have permission to edit this page, because you are not logged in.")
    ).to_be_visible()
    expect(page.locator("textarea")).to_be_empty()


def test_source_page_wrong_casing(page: Page):
    """Page with different casing should suggest to redirect."""
    page.goto("http://localhost:8080/en/main%20page2.mediawiki")

    expect(page.locator('text="en/main page2" does not exist; did you mean Main Page2?')).to_be_visible()


def test_source_page_invalid(page: Page):
    """Requesting source of an invalid page."""
    page.goto("http://localhost:8080/Main%20Page.mediawiki")

    expect(page.locator('text=Page name "Main Page" is missing either a language or a namespace.')).to_be_visible()
