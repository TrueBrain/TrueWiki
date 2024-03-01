from playwright.sync_api import Page, expect


def test_sitemap_page(page: Page):
    """Check if the sitemap is being generated correctly."""
    page.goto("view-source:http://localhost:8080/sitemap.xml")
    expect(page.locator("text=http://www.sitemaps.org/schemas/sitemap/0.9")).to_be_visible()
    expect(page.locator("text=<loc>http://localhost:8080/en/Main%20Page</loc>")).to_be_visible()
    expect(page.locator("text=<loc>http://localhost:8080/en/Main%20Page2</loc>")).to_be_visible()
    expect(page.locator("text=http://localhost:8080/de/").nth(1)).to_be_visible()


def test_sitemap_page_cached(page: Page):
    """Second call loads it from the cache. Ensure it is still correct."""
    page.goto("view-source:http://localhost:8080/sitemap.xml")
    expect(page.locator("text=http://www.sitemaps.org/schemas/sitemap/0.9")).to_be_visible()
    expect(page.locator("text=<loc>http://localhost:8080/en/Main%20Page</loc>")).to_be_visible()
    expect(page.locator("text=<loc>http://localhost:8080/en/Main%20Page2</loc>")).to_be_visible()
    expect(page.locator("text=http://localhost:8080/de/").nth(1)).to_be_visible()


def test_sitemap_invalidate(page: Page, login):
    """Create a new page, which invalidates the sitemap."""
    page.goto("http://localhost:8080/en/Sitemap%20Change")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()

    page.locator("[name=content]").fill("Invalidate Sitemap")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/en/Sitemap%20Change")

    expect(page).to_have_title("Unnamed | Sitemap Change")
    expect(page.locator("text=Invalidate Sitemap")).to_be_visible()


def test_sitemap_page_after_change(page: Page):
    """Check if the new page ended up in the sitemap."""
    page.goto("view-source:http://localhost:8080/sitemap.xml")
    expect(page.locator("text=http://www.sitemaps.org/schemas/sitemap/0.9")).to_be_visible()
    expect(page.locator("text=<loc>http://localhost:8080/en/Main%20Page</loc>")).to_be_visible()
    expect(page.locator("text=<loc>http://localhost:8080/en/Main%20Page2</loc>")).to_be_visible()
    expect(page.locator("text=http://localhost:8080/de/").nth(1)).to_be_visible()
    expect(page.locator("text=<loc>http://localhost:8080/en/Sitemap%20Change</loc>")).to_be_visible()
