from playwright.sync_api import Page, expect


def test_main_page(page: Page):
    page.goto("http://localhost:8080/")
    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
