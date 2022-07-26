from playwright.sync_api import Page, expect


def test_robots_page(page: Page):
    """Check if the robots.txt is being generated correctly."""
    page.goto("http://localhost:8080/robots.txt")
    expect(page.locator("text=User-agent")).to_be_visible()
    expect(page.locator("text=Sitemap: http://localhost:8080/sitemap.xml")).to_be_visible()
