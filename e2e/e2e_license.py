from playwright.sync_api import Page, expect


def test_license_page(page: Page):
    """Check that the license page is actually loading."""
    page.goto("http://localhost:8080/License")
    expect(page).to_have_title("Unnamed | License")
    expect(page.locator("#pagename")).to_be_visible()
    expect(page.locator("#pagename")).to_have_text("License")
    expect(page.locator("text=Content is available under Unlicensed")).to_be_visible()
