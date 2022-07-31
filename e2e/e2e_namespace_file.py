from playwright.sync_api import Page, expect


def test_file_view_empty(page: Page):
    """Check if we can view an empty file."""
    page.goto("http://localhost:8080/")

    image = page.locator("text=File:en/Test.png")
    expect(image).to_be_visible()
    with page.expect_navigation():
        image.click()
    page.wait_for_url("/File/en/Test.png")

    expect(page.locator("text=There is currently no file with that name.")).to_be_visible()


def test_file_view_bad_extension(page: Page):
    """Check if we can view a file with a bad extension."""
    page.goto("http://localhost:8080/File/en/Test.image")

    expect(
        page.locator(
            'text=Page name "File/en/Test.image" in the File namespace should'
            ' end with either ".png", ".gif", or ".jpeg".'
        )
    ).to_be_visible()


def test_file_edit_empty(page: Page, login):
    """Check that we can edit files without uploading."""
    page.goto("http://localhost:8080/File/en/Empty.png")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Empty.png")

    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Empty.png")

    expect(page).to_have_title("Unnamed | Empty.png")
    expect(page.locator("text=This file has no description yet.")).to_be_visible()


def test_file_edit_without_image(page: Page, login):
    """Check that we can edit files without uploading."""
    page.goto("http://localhost:8080/File/en/Test.png")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.png")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.png")

    expect(page).to_have_title("Unnamed | Test.png")
    expect(page.locator("text=My First Upload")).to_be_visible()
    expect(page.locator("text=(no file uploaded yet)")).to_be_visible()


def test_file_upload_invalid_image(page: Page, login):
    """Check if uploading invalid image doesn't actually work."""
    page.goto("http://localhost:8080/File/en/Test.png")

    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.png")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/invalid.txt")
    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.png")

    expect(
        page.locator('text=Uploaded file "invalid.txt" is not a valid image. Only PNG, GIF, and JPEG is supported.')
    ).to_be_visible()


def test_file_upload_invalid_png(page: Page, login):
    """Check if uploading invalid PNG doesn't actually work."""
    page.goto("http://localhost:8080/File/en/Test.png")

    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.png")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/invalid.png")
    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.png")

    expect(page.locator('text=Uploaded file "invalid.png" is not a valid PNG image.')).to_be_visible()


def test_file_upload_invalid_gif(page: Page, login):
    """Check if uploading invalid GIF doesn't actually work."""
    page.goto("http://localhost:8080/File/en/Test.gif")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.gif")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/invalid.gif")
    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.gif")

    expect(page.locator('text=Uploaded file "invalid.gif" is not a valid GIF image.')).to_be_visible()


def test_file_upload_invalid_jpeg(page: Page, login):
    """Check if uploading invalid JPEG doesn't actually work."""
    page.goto("http://localhost:8080/File/en/Test.jpeg")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.jpeg")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/invalid.jpeg")
    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.jpeg")

    expect(page.locator('text=Uploaded file "invalid.jpeg" is not a valid JPEG image.')).to_be_visible()


def test_file_upload_wrong_gif(page: Page, login):
    """Check if uploading a GIF on a .png doesn't actually work."""
    page.goto("http://localhost:8080/File/en/Test.png")

    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.png")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/test.gif")
    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.png")

    expect(page.locator('text=Page name "File/en/Test.png" should end with ".gif" if uploading a GIF.')).to_be_visible()


def test_file_upload_wrong_jpeg(page: Page, login):
    """Check if uploading a JPEG on a .png doesn't actually work."""
    page.goto("http://localhost:8080/File/en/Test.png")

    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.png")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/test.jpeg")
    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.png")

    expect(
        page.locator('text=Page name "File/en/Test.png" should end with ".jpeg" if uploading a JPEG.')
    ).to_be_visible()


def test_file_upload_png(page: Page, login):
    """Check that we can upload PNG images."""
    page.goto("http://localhost:8080/File/en/Test.png")

    create = page.locator("text=Edit Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.png")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/test.png")
    page.locator("[name=content]").fill("My First Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.png")

    expect(page).to_have_title("Unnamed | Test.png")
    expect(page.locator("text=My First Upload")).to_be_visible()
    expect(page.locator('h3:has-text("Used on pages")')).to_be_visible()
    expect(page.locator("main >> text=Unnamed's Wiki")).to_be_visible()
    expect(page.locator("text=Filesize: 2.81 KiB")).to_be_visible()


def test_file_upload_wrong_png(page: Page, login):
    """Check if uploading a PNG on a .gif doesn't actually work."""
    page.goto("http://localhost:8080/File/en/Test.gif")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.gif")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/test.png")
    page.locator("[name=content]").fill("My Second Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.gif")

    expect(page.locator('text=Page name "File/en/Test.gif" should end with ".png" if uploading a PNG.')).to_be_visible()


def test_file_upload_gif(page: Page, login):
    """Check that we can upload GIF images."""
    page.goto("http://localhost:8080/File/en/Test.gif")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.gif")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/test.gif")
    page.locator("[name=content]").fill("My Second Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.gif")

    expect(page).to_have_title("Unnamed | Test.gif")
    expect(page.locator("text=My Second Upload")).to_be_visible()
    expect(page.locator("text=Filesize: 2.13 KiB")).to_be_visible()


def test_file_upload_jpeg(page: Page, login):
    """Check that we can upload JPEG images."""
    page.goto("http://localhost:8080/File/en/Test.jpeg")

    create = page.locator("text=Create Page")
    expect(create).to_be_visible()
    with page.expect_navigation():
        create.click()
    page.wait_for_url("/edit/File/en/Test.jpeg")

    expect(page.locator("text=Upload new file")).to_be_visible()

    page.locator("[name=file]").set_input_files("e2e/test.jpeg")
    page.locator("[name=content]").fill("My Third Upload\n[[Category:en/MyPictures]]")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.jpeg")

    expect(page).to_have_title("Unnamed | Test.jpeg")
    expect(page.locator("text=My Third Upload")).to_be_visible()
    expect(page.locator("text=Filesize: 3.05 KiB")).to_be_visible()


def test_file_cannot_rename(page: Page, login):
    """Check if we cannot rename a file that is being used by another page."""
    page.goto("http://localhost:8080/File/en/Test.png")

    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("/edit/File/en/Test.png")

    expect(page.locator("text=Pages cannot be renamed if they are used by other pages.")).to_be_visible()


def test_file_cannot_rename_extension(page: Page, login):
    """Check if we cannot rename the extension of a file."""
    page.goto("http://localhost:8080/File/en/Test.jpeg")

    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("/edit/File/en/Test.jpeg")

    page.locator("[name=page]").fill("File/en/Test2.png")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test.jpeg")

    expect(page.locator("text=Cannot rename extension of a file.")).to_be_visible()


def test_file_rename(page: Page, login):
    """Check if we can actually rename a file."""
    page.goto("http://localhost:8080/File/en/Test.jpeg")

    edit = page.locator("text=Edit Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("/edit/File/en/Test.jpeg")

    page.locator("[name=page]").fill("File/en/Test2.jpeg")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/File/en/Test2.jpeg")


def test_file_root(page: Page):
    """Check if the file of the root is listing the right pages."""
    page.goto("http://localhost:8080/File/en/Test.png")

    folder = page.locator("nav >> text=File")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("/File/")

    expect(page.locator("text=A list of all the languages which have one or more files.")).to_be_visible()
    expect(page.locator('main >> a:has-text("en")')).to_be_visible()


def test_file_language(page: Page):
    """Check if the file of the language is listing the right pages."""
    page.goto("http://localhost:8080/File/en/Test.png")

    folder = page.locator("nav >> text=en")
    expect(folder).to_be_visible()
    with page.expect_navigation():
        folder.click()
    page.wait_for_url("/File/en/")

    expect(page.locator("text=All the files that belong to this language.")).to_be_visible()
    expect(page.locator('main >> a:has-text("Test.png")')).to_be_visible()
    expect(page.locator('main >> a:has-text("Test.gif")')).to_be_visible()
    expect(page.locator('main >> a:has-text("Test2.jpeg")')).to_be_visible()


def test_file_folder(page: Page):
    """Check if the file of the folder is listing the right pages."""
    page.goto("http://localhost:8080/File/en/folder/")

    expect(page.locator("text=All the files that belong to this folder.")).to_be_visible()


def test_file_cannot_edit_root(page: Page, login):
    """Check you cannot edit the root file in a folder."""
    page.goto("http://localhost:8080/File/en/Test2.png")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("/edit/File/en/Test2.png")

    page.locator("[name=page]").fill("File/en/Testing/Main Page")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/File/en/Test2.png")

    expect(
        page.locator('text=Page name "File/en/Testing/Main Page" is invalid, as it is automatically generated.')
    ).to_be_visible()


def test_file_cannot_edit_language(page: Page, login):
    """Check you cannot edit the root file in a language."""
    page.goto("http://localhost:8080/File/en/Test2.png")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("/edit/File/en/Test2.png")

    page.locator("[name=page]").fill("File/en/Main Page")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/File/en/Test2.png")

    expect(
        page.locator('text=Page name "File/en/Main Page" is invalid, as it is automatically generated.')
    ).to_be_visible()


def test_file_edit_missing_language(page: Page, login):
    """Ensure the language of a file has to exist."""
    page.goto("http://localhost:8080/File/en/Test2.png")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("/edit/File/en/Test2.png")

    page.locator("[name=page]").fill("File/test")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/File/en/Test2.png")

    expect(page.locator('text=Page name "File/test" is missing a language code.')).to_be_visible()


def test_file_edit_invalid_language(page: Page, login):
    """Ensure the language of a file is valid."""
    page.goto("http://localhost:8080/File/en/Test2.png")

    edit = page.locator("text=Create Page")
    expect(edit).to_be_visible()
    with page.expect_navigation():
        edit.click()
    page.wait_for_url("/edit/File/en/Test2.png")

    page.locator("[name=page]").fill("File/zz/test")
    page.locator("[name=content]").fill("Some text")
    with page.expect_navigation():
        page.locator("[name=save]").click()
    page.wait_for_url("/edit/File/en/Test2.png")

    expect(page.locator('text=Page name "File/zz/test" is in language "zz" that does not exist.')).to_be_visible()


def test_files_linked_category(page: Page):
    """Check if the files are linked from the category."""
    page.goto("http://localhost:8080/File/en/Test.png")

    category = page.locator("text=MyPictures")
    expect(category).to_be_visible()
    with page.expect_navigation():
        category.click()

    page.wait_for_url("/Category/en/MyPictures")

    expect(page.locator('h2:has-text("Files")')).to_be_visible()
    expect(page.locator("main >> text=Test.png")).to_be_visible()
    expect(page.locator("main >> text=Test.gif")).to_be_visible()
    expect(page.locator("main >> text=Test2.jpeg")).to_be_visible()


def test_file_view(page: Page, login):
    """Check if we can view images and links."""
    page.goto("http://localhost:8080/")

    expect(page.locator('img[alt="/File/en/Test.png"]')).to_be_visible()
    expect(page.locator("text=Test.png")).to_be_visible()
