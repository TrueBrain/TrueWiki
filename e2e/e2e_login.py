from playwright.sync_api import Page, expect


def test_login_page(page: Page):
    page.goto("http://localhost:8080/")

    # Check the login button is on the page.
    login = page.locator("text=Login")
    expect(login).to_be_visible()
    expect(login).to_have_attribute("href", "/user/login?location=en/Main%20Page")
    with page.expect_navigation():
        login.click()
    page.wait_for_url("/user/login?location=en/Main%20Page")

    # Make sure we end up on the login page.
    expect(page).to_have_title("Unnamed | Login")


def test_login_flow(page: Page):
    page.goto("http://localhost:8080/user/login")

    # We run the test in developer-mode, as we lack credentials for SSOs.
    login = page.locator("text=Login as developer")
    expect(login).to_be_visible()
    with page.expect_navigation():
        login.click()
    page.wait_for_url("/user/login")

    # Fill in the developer-login form.
    page.locator("[name=username]").fill("test")
    with page.expect_navigation():
        page.locator("[type=submit]").click()

    # Make sure we end up on the main page while being logged in.
    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    logout = page.locator("text=Logout (test)")
    expect(logout).to_be_visible()

    # Now logout.
    with page.expect_navigation():
        logout.click()
    page.wait_for_url("/en/Main%20Page")
    expect(page.locator("text=Login")).to_be_visible()
