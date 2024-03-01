from playwright.sync_api import Page, expect


def test_category_linked(page: Page):
    """Check if the Main Page is in a category."""
    page.goto("http://localhost:8080/")

    category = page.locator("text=MyPages")
    expect(category).to_be_visible()
    with page.expect_navigation():
        category.click()

    page.wait_for_url("http://localhost:8080/Category/en/MyPages")

    expect(page.locator("main >> text=Unnamed's Wiki")).to_be_visible()
    expect(page.locator("text=Main Page2")).to_be_visible()


def test_category_edit_page(page: Page, login):
    """Check if we can actually edit the category page."""
    page.goto("http://localhost:8080/Category/en/MyPages")

    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/MyPages")

    page.locator("[name=content]").fill("Our category\n\n[[Category:en/folder/OtherPages]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/Category/en/MyPages")

    expect(page.locator("text=Our category")).to_be_visible()
    expect(page.locator("text=OtherPages")).to_be_visible()


def test_category_linked_category(page: Page):
    """Check if the categories are linked from other categories."""
    page.goto("http://localhost:8080/Category/en/MyPages")

    category = page.locator("text=OtherPages")
    expect(category).to_be_visible()
    with page.expect_navigation():
        category.click()

    page.wait_for_url("http://localhost:8080/Category/en/folder/OtherPages")

    expect(page.locator("text=Subcategories")).to_be_visible()
    expect(page.locator("main >> text=MyPages")).to_be_visible()


def test_category_edit_empty(page: Page, login):
    """Check if we can actually make the category page text empty."""
    page.goto("http://localhost:8080/Category/en/folder/OtherPages")

    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/folder/OtherPages")

    page.locator("[name=content]").fill("")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/Category/en/folder/OtherPages")

    expect(page.locator("text=There is currently no additional text for this category.")).to_be_visible()


def test_category_cannot_edit_root(page: Page, login):
    """Check you cannot edit the root category in a language."""
    page.goto("http://localhost:8080/Category/en/")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/")

    page.locator("[name=page]").fill("Category/en/Main Page")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/")

    expect(
        page.locator('text=Page name "Category/en/Main Page" is invalid, as it is automatically generated.')
    ).to_be_visible()


def test_category_edit_missing_language(page: Page, login):
    """Ensure the language of a category has to exist."""
    page.goto("http://localhost:8080/Category/en/")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/")

    page.locator("[name=page]").fill("Category/test")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/")

    expect(page.locator('text=Page name "Category/test" is missing a language code.')).to_be_visible()


def test_category_edit_invalid_language(page: Page, login):
    """Ensure the language of a category is valid."""
    page.goto("http://localhost:8080/Category/en/")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/")

    page.locator("[name=page]").fill("Category/zz/test")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("http://localhost:8080/edit/Category/en/")

    expect(page.locator('text=Page name "Category/zz/test" is in language "zz" that does not exist.')).to_be_visible()


def test_category_root(page: Page):
    """Check if the category of the root is listing the right pages."""
    page.goto("http://localhost:8080/Category/en/MyPages")

    folder = page.locator("nav >> text=Category")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("http://localhost:8080/Category/")

    expect(page.locator("text=A list of all the languages which have one or more categories.")).to_be_visible()
    expect(page.locator('main >> a:has-text("en")')).to_be_visible()


def test_category_language(page: Page):
    """Check if the category of the language is listing the right pages."""
    page.goto("http://localhost:8080/Category/en/MyPages")

    folder = page.locator("nav >> text=en")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("http://localhost:8080/Category/en/")

    expect(page.locator("text=All the categories that belong to this language.")).to_be_visible()
    expect(page.locator('main >> a:has-text("MyPages")')).to_be_visible()
    expect(page.locator('main >> a:has-text("folder")')).to_be_visible()


def test_category_page_empty(page: Page):
    """Check if a non-existing category page is in fact empty."""
    page.goto("http://localhost:8080/Category/en/MyEmpty")

    expect(page.locator("text=There is currently no additional text for this category.")).to_be_visible()
    expect(page.locator("text=this category is empty")).to_be_visible()


def test_category_folder_empty(page: Page):
    """Check if a non-existing category folder is in fact empty."""
    page.goto("http://localhost:8080/Category/en/MyEmpty/")

    expect(page.locator("text=All the categories that belong to this folder.")).to_be_visible()
    expect(page.locator("text=this folder is empty")).to_be_visible()


def test_category_folder(page: Page):
    """Check if a existing category folder is actually showing the subcategories."""
    page.goto("http://localhost:8080/Category/en/folder/")

    expect(page.locator("text=All the categories that belong to this folder.")).to_be_visible()
    expect(page.locator('main >> a:has-text("OtherPages")')).to_be_visible()
