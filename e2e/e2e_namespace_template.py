from playwright.sync_api import Page, expect


def test_template_non_existing(page: Page):
    """Check that references to templates that don't exist are links."""
    page.goto("http://localhost:8080/")

    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator('a:has-text("Template:en/Summary")')).to_be_visible()


def test_template_edit(page: Page, login):
    """Check if we can edit a template."""
    page.goto("http://localhost:8080/Template/en/Summary")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/Summary")

    page.locator("[name=content]").fill("My First Template\n[[Category:en/MyTemplates]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/Template/en/Summary")

    expect(page).to_have_title("Unnamed | Summary")
    expect(page.locator("text=My First Template")).to_be_visible()


def test_template_create_link(page: Page, login):
    """Create a template linking to another template."""
    page.goto("http://localhost:8080/Template/en/OtherTemplate")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/OtherTemplate")

    page.locator("[name=content]").fill("{{en/Summary}}")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/Template/en/OtherTemplate")

    expect(page).to_have_title("Unnamed | OtherTemplate")
    expect(page.locator("text=My First Template")).to_be_visible()


def test_template_create_empty(page: Page, login):
    """Create an empty template."""
    page.goto("http://localhost:8080/Template/en/Empty")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/Empty")

    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/Template/en/Empty")

    expect(page).to_have_title("Unnamed | Empty")
    expect(page.locator("text=There is currently no text on this page.")).to_be_visible()


def test_template_link(page: Page, login):
    """Check if the links on the edit page of Templates are correct."""
    page.goto("http://localhost:8080/Template/en/Summary")

    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/Summary")

    expect(page.locator("main >> text=OtherTemplate")).to_be_visible()
    expect(page.locator("main >> text=Unnamed's Wiki")).to_be_visible()
    expect(page.locator("main >> text=Main Page2")).to_be_visible()


def test_template_link_page(page: Page, login):
    """Check if the links on the edit page of a page using a Template are correct."""
    page.goto("http://localhost:8080/")

    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("http://localhost:8080/edit/en/Main%20Page")

    expect(page.locator('a:has-text("Summary")')).to_be_visible()


def test_template_existing(page: Page):
    """Check that references to templates that do exist are resolved."""
    page.goto("http://localhost:8080/")

    expect(page).to_have_title("Unnamed | Unnamed's Wiki")
    expect(page.locator("text=My First Template")).to_be_visible()


def test_template_root(page: Page):
    """Check if the template of the root is listing the right pages."""
    page.goto("http://localhost:8080/Template/en/Summary")

    folder = page.locator("nav >> text=Template")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("http://localhost:8080/Template/")

    expect(page.locator("text=A list of all the languages which have one or more templates.")).to_be_visible()
    expect(page.locator('main >> a:has-text("en")')).to_be_visible()


def test_template_language(page: Page):
    """Check if the template of the language is listing the right pages."""
    page.goto("http://localhost:8080/Template/en/Summary")

    folder = page.locator("nav >> text=en")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("http://localhost:8080/Template/en/")

    expect(page.locator("text=All the templates that belong to this language.")).to_be_visible()
    expect(page.locator('main >> a:has-text("Summary")')).to_be_visible()
    expect(page.locator('main >> a:has-text("OtherTemplate")')).to_be_visible()


def test_template_cannot_edit_root(page: Page, login):
    """Check you cannot edit the root template in a language."""
    page.goto("http://localhost:8080/Template/en/")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/")

    page.locator("[name=page]").fill("Template/en/Main Page")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/")

    expect(
        page.locator('text=Page name "Template/en/Main Page" is invalid, as it is automatically generated.')
    ).to_be_visible()


def test_template_edit_missing_language(page: Page, login):
    """Ensure the language of a template has to exist."""
    page.goto("http://localhost:8080/Template/en/")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/")

    page.locator("[name=page]").fill("Template/test")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/")

    expect(page.locator('text=Page name "Template/test" is missing a language code.')).to_be_visible()


def test_template_edit_invalid_language(page: Page, login):
    """Ensure the language of a template is valid."""
    page.goto("http://localhost:8080/Template/en/")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/")

    page.locator("[name=page]").fill("Template/zz/test")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/")

    expect(page.locator('text=Page name "Template/zz/test" is in language "zz" that does not exist.')).to_be_visible()


def test_template_linked_category(page: Page):
    """Check if the templates are linked from the category."""
    page.goto("http://localhost:8080/Template/en/Summary")

    category = page.locator("text=MyTemplates")
    expect(category).to_be_visible()
    with page.expect_navigation():
        category.click()

    page.wait_for_url("http://localhost:8080/Category/en/MyTemplates")

    expect(page.locator('h2:has-text("Pages")')).to_be_visible()
    expect(page.locator('h2:has-text("Templates")')).to_be_visible()
    expect(page.locator("main >> text=Unnamed's Wiki")).to_be_visible()
    expect(page.locator("main >> text=Summary")).to_be_visible()


def test_template_cannot_rename(page: Page, login):
    """Check you cannot rename a template that is used by another page."""
    page.goto("http://localhost:8080/Template/en/Summary")

    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Template/en/Summary")

    expect(page.locator("text=Pages cannot be renamed if they are used by other pages.")).to_be_visible()
