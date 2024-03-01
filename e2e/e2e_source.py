from playwright.sync_api import Page, expect


def test_source_page(page: Page):
    """Check if we can view the source page of the main page."""
    page.goto("http://localhost:8080/")

    source = page.locator("text=View Source")
    expect(source).to_be_visible()
    with page.expect_navigation():
        source.click()
    page.wait_for_url("http://localhost:8080/en/Main%20Page.mediawiki")

    expect(
        page.locator("text=You do not have permission to edit this page, because you are not logged in.")
    ).to_be_visible()
    expect(page.locator("textarea")).to_have_text(
        "[[Translation:en/Main Page]]\nMy Third Edit\n\n[[Category:en/MyPages]]\n{{en/Summary}}"
        "\n{{Page:en/Empty}}\n[[File:en/Test.png]]\n[[Media:en/Test.png]]"
    )
    expect(page.locator("text=My Third Edit")).to_be_visible()

    expect(page.locator("text=No templates used")).not_to_be_visible()
    expect(page.locator("text=Not used on any page")).to_be_visible()

    # Entries of the templates.
    expect(page.locator('a:has-text("Summary")')).to_be_visible()


def test_source_template(page: Page):
    """Check if we can view the source page of a template."""
    page.goto("http://localhost:8080/Template/en/Summary")

    source = page.locator("text=View Source")
    expect(source).to_be_visible()
    with page.expect_navigation():
        source.click()
    page.wait_for_url("http://localhost:8080/Template/en/Summary.mediawiki")

    expect(
        page.locator("text=You do not have permission to edit this page, because you are not logged in.")
    ).to_be_visible()
    expect(page.locator("textarea")).to_have_text("My First Template\n[[Category:en/MyTemplates]]")
    expect(page.locator("text=No templates used")).to_be_visible()
    expect(page.locator("text=Not used on any page")).not_to_be_visible()

    # Entries of the "used on pages".
    expect(page.locator("main >> text=Unnamed's Wiki")).to_be_visible()
    expect(page.locator("main >> text=Main Page2")).to_be_visible()


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
