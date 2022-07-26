from playwright.sync_api import Page, expect


def test_main_page(page: Page):
    """Check that the main page is actually loading."""
    page.goto("http://localhost:8080/")
    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator("text=Powered by TrueWiki")).to_be_visible()


def test_healtz(page: Page):
    """Make sure the health-check URL is functional."""
    page.goto("http://localhost:8080/healthz")
    expect(page.locator("text=200: OK")).to_be_visible()
