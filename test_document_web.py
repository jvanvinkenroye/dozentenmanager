"""
Test document management web interface using Playwright.

This script demonstrates the document management functionality by:
1. Opening the documents list page
2. Testing document upload form
3. Testing bulk upload form
4. Testing submissions page
5. Testing email import page
6. Testing document filtering
"""

import asyncio
import logging
import os
import tempfile

from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5002"


async def test_document_list_page(page):
    """Test the document list page."""
    logger.info("=" * 60)
    logger.info("Testing Document List Page")
    logger.info("=" * 60)

    # Navigate to documents page
    logger.info("Opening documents page...")
    await page.goto(f"{BASE_URL}/documents/")
    await page.wait_for_load_state("networkidle")

    # Verify page title
    title = await page.title()
    logger.info(f"Page title: {title}")
    assert "Dokumente" in title, f"Expected 'Dokumente' in title, got '{title}'"

    # Verify page heading
    heading = await page.locator("h1.title").text_content()
    logger.info(f"Page heading: {heading}")
    assert "Dokumente" in heading, f"Expected 'Dokumente' in heading, got '{heading}'"

    # Verify navigation buttons exist
    upload_button = await page.locator("a:has-text('Hochladen')").count()
    bulk_upload_button = await page.locator("a:has-text('Bulk-Upload')").count()
    submissions_button = await page.locator("a:has-text('Einreichungen')").count()
    email_import_button = await page.locator("a:has-text('E-Mail-Import')").count()

    logger.info(f"Upload button present: {upload_button > 0}")
    logger.info(f"Bulk-Upload button present: {bulk_upload_button > 0}")
    logger.info(f"Submissions button present: {submissions_button > 0}")
    logger.info(f"E-Mail-Import button present: {email_import_button > 0}")

    assert upload_button > 0, "Upload button not found"
    assert bulk_upload_button > 0, "Bulk-Upload button not found"
    assert submissions_button > 0, "Submissions button not found"
    assert email_import_button > 0, "E-Mail-Import button not found"

    # Verify filter form exists
    filter_form = await page.locator("form").count()
    logger.info(f"Filter form present: {filter_form > 0}")

    # Check for course filter dropdown
    course_select = await page.locator("select[name='course_id']").count()
    logger.info(f"Course filter dropdown: {course_select > 0}")

    # Check for student filter dropdown
    student_select = await page.locator("select[name='student_id']").count()
    logger.info(f"Student filter dropdown: {student_select > 0}")

    # Check for file type filter
    file_type_select = await page.locator("select[name='file_type']").count()
    logger.info(f"File type filter dropdown: {file_type_select > 0}")

    # Check for status filter
    status_select = await page.locator("select[name='status']").count()
    logger.info(f"Status filter dropdown: {status_select > 0}")

    # Check if documents exist or "no documents" message is shown
    doc_table = await page.locator("table tbody tr").count()
    no_docs_message = await page.locator("text=Keine Dokumente gefunden").count()

    if doc_table > 0:
        logger.info(f"Found {doc_table} documents in the list")
    elif no_docs_message > 0:
        logger.info("No documents found - empty state displayed correctly")
    else:
        logger.warning("Neither documents nor empty state message found")

    logger.info("✓ Document list page test passed!")
    return True


async def test_document_upload_page(page):
    """Test the document upload page."""
    logger.info("=" * 60)
    logger.info("Testing Document Upload Page")
    logger.info("=" * 60)

    # Navigate to upload page
    logger.info("Opening upload page...")
    await page.goto(f"{BASE_URL}/documents/upload")
    await page.wait_for_load_state("networkidle")

    # Verify page heading
    heading = await page.locator("h1.title").text_content()
    logger.info(f"Page heading: {heading}")
    assert "Dokument hochladen" in heading, "Expected 'Dokument hochladen' in heading"

    # Verify form elements exist
    file_input = await page.locator("input[type='file']").count()
    logger.info(f"File input present: {file_input > 0}")
    assert file_input > 0, "File input not found"

    # Verify enrollment dropdown exists
    enrollment_select = await page.locator("select[name='enrollment_id']").count()
    logger.info(f"Enrollment dropdown present: {enrollment_select > 0}")

    # Verify submission type dropdown exists
    type_select = await page.locator("select[name='submission_type']").count()
    logger.info(f"Submission type dropdown present: {type_select > 0}")

    # Verify notes textarea exists
    notes_input = await page.locator("textarea[name='notes']").count()
    logger.info(f"Notes textarea present: {notes_input > 0}")

    # Verify submit button exists
    submit_button = await page.locator("button[type='submit']").count()
    logger.info(f"Submit button present: {submit_button > 0}")
    assert submit_button > 0, "Submit button not found"

    # Verify cancel link exists
    cancel_link = await page.locator("a:has-text('Abbrechen')").count()
    logger.info(f"Cancel link present: {cancel_link > 0}")

    logger.info("✓ Document upload page test passed!")
    return True


async def test_bulk_upload_page(page):
    """Test the bulk upload page."""
    logger.info("=" * 60)
    logger.info("Testing Bulk Upload Page")
    logger.info("=" * 60)

    # Navigate to bulk upload page
    logger.info("Opening bulk upload page...")
    await page.goto(f"{BASE_URL}/documents/bulk-upload")
    await page.wait_for_load_state("networkidle")

    # Verify page heading
    heading = await page.locator("h1.title").text_content()
    logger.info(f"Page heading: {heading}")
    assert "Bulk-Upload" in heading, "Expected 'Bulk-Upload' in heading"

    # Verify multiple file input exists
    file_input = await page.locator("input[type='file']").count()
    logger.info(f"File input present: {file_input > 0}")
    assert file_input > 0, "File input not found"

    # Verify course dropdown exists
    course_select = await page.locator("select[name='course_id']").count()
    logger.info(f"Course dropdown present: {course_select > 0}")

    # Verify submission type dropdown exists
    type_select = await page.locator("select[name='submission_type']").count()
    logger.info(f"Submission type dropdown present: {type_select > 0}")

    # Verify submit button exists
    submit_button = await page.locator("button[type='submit']").count()
    logger.info(f"Submit button present: {submit_button > 0}")
    assert submit_button > 0, "Submit button not found"

    logger.info("✓ Bulk upload page test passed!")
    return True


async def test_submissions_page(page):
    """Test the submissions page."""
    logger.info("=" * 60)
    logger.info("Testing Submissions Page")
    logger.info("=" * 60)

    # Navigate to submissions page
    logger.info("Opening submissions page...")
    await page.goto(f"{BASE_URL}/documents/submissions")
    await page.wait_for_load_state("networkidle")

    # Verify page heading
    heading = await page.locator("h1.title").text_content()
    logger.info(f"Page heading: {heading}")
    assert "Einreichungen" in heading, "Expected 'Einreichungen' in heading"

    # Check if submissions exist or "no submissions" message is shown
    submission_table = await page.locator("table tbody tr").count()
    no_submissions_message = await page.locator("text=Keine Einreichungen gefunden").count()

    if submission_table > 0:
        logger.info(f"Found {submission_table} submissions in the list")
    elif no_submissions_message > 0:
        logger.info("No submissions found - empty state displayed correctly")
    else:
        logger.warning("Neither submissions nor empty state message found")

    # Verify filter form exists
    filter_form = await page.locator("form").count()
    logger.info(f"Filter form present: {filter_form > 0}")

    logger.info("✓ Submissions page test passed!")
    return True


async def test_email_import_page(page):
    """Test the email import page."""
    logger.info("=" * 60)
    logger.info("Testing Email Import Page")
    logger.info("=" * 60)

    # Navigate to email import page
    logger.info("Opening email import page...")
    await page.goto(f"{BASE_URL}/documents/email-import")
    await page.wait_for_load_state("networkidle")

    # Verify page heading
    heading = await page.locator("h1.title").text_content()
    logger.info(f"Page heading: {heading}")
    assert "E-Mail-Import" in heading, "Expected 'E-Mail-Import' in heading"

    # Verify file input exists
    file_input = await page.locator("input[type='file']").count()
    logger.info(f"File input present: {file_input > 0}")
    assert file_input > 0, "File input not found"

    # Verify course dropdown exists
    course_select = await page.locator("select[name='course_id']").count()
    logger.info(f"Course dropdown present: {course_select > 0}")

    # Verify submit button exists
    submit_button = await page.locator("button[type='submit']").count()
    logger.info(f"Submit button present: {submit_button > 0}")
    assert submit_button > 0, "Submit button not found"

    logger.info("✓ Email import page test passed!")
    return True


async def test_navigation_from_navbar(page):
    """Test navigation to documents from the main navbar."""
    logger.info("=" * 60)
    logger.info("Testing Navigation from Navbar")
    logger.info("=" * 60)

    # Navigate to home page
    logger.info("Opening home page...")
    await page.goto(BASE_URL)
    await page.wait_for_load_state("networkidle")

    # Click on Documents link in navbar
    logger.info("Clicking on 'Dokumente' in navbar...")
    await page.click("a.navbar-item:has-text('Dokumente')")
    await page.wait_for_load_state("networkidle")

    # Verify we're on the documents page
    current_url = page.url
    logger.info(f"Current URL: {current_url}")
    assert "/documents" in current_url, f"Expected '/documents' in URL, got '{current_url}'"

    # Verify page heading
    heading = await page.locator("h1.title").text_content()
    logger.info(f"Page heading: {heading}")
    assert "Dokumente" in heading, "Expected 'Dokumente' in heading"

    logger.info("✓ Navigation from navbar test passed!")
    return True


async def test_document_filter_functionality(page):
    """Test the document filter functionality."""
    logger.info("=" * 60)
    logger.info("Testing Document Filter Functionality")
    logger.info("=" * 60)

    # Navigate to documents page
    logger.info("Opening documents page...")
    await page.goto(f"{BASE_URL}/documents/")
    await page.wait_for_load_state("networkidle")

    # Get initial state
    initial_url = page.url
    logger.info(f"Initial URL: {initial_url}")

    # Try selecting a file type filter
    file_type_options = await page.locator("select[name='file_type'] option").all()
    if len(file_type_options) > 1:
        # Select the second option (first is usually "All")
        await page.select_option("select[name='file_type']", index=1)
        logger.info("Selected file type filter")

        # Click filter button
        await page.click("button:has-text('Filtern')")
        await page.wait_for_load_state("networkidle")

        # Check URL has changed with filter parameter
        filtered_url = page.url
        logger.info(f"Filtered URL: {filtered_url}")

        if "file_type=" in filtered_url:
            logger.info("✓ Filter parameter added to URL")
        else:
            logger.info("Filter parameter not in URL (might be empty filter)")
    else:
        logger.info("No file type filter options available for testing")

    logger.info("✓ Document filter functionality test passed!")
    return True


async def test_breadcrumb_navigation(page):
    """Test breadcrumb navigation on document pages."""
    logger.info("=" * 60)
    logger.info("Testing Breadcrumb Navigation")
    logger.info("=" * 60)

    # Navigate to documents page
    logger.info("Opening documents page...")
    await page.goto(f"{BASE_URL}/documents/")
    await page.wait_for_load_state("networkidle")

    # Check breadcrumb exists
    breadcrumb = await page.locator("nav.breadcrumb").count()
    logger.info(f"Breadcrumb navigation present: {breadcrumb > 0}")

    if breadcrumb > 0:
        # Check Home link in breadcrumb
        home_link = await page.locator("nav.breadcrumb a:has-text('Home')").count()
        logger.info(f"Home link in breadcrumb: {home_link > 0}")

        # Check current page indicator
        current_page = await page.locator("nav.breadcrumb li.is-active").count()
        logger.info(f"Current page indicator: {current_page > 0}")

        # Click Home link and verify navigation
        if home_link > 0:
            await page.click("nav.breadcrumb a:has-text('Home')")
            await page.wait_for_load_state("networkidle")

            current_url = page.url
            logger.info(f"After clicking Home: {current_url}")
            assert current_url == f"{BASE_URL}/" or current_url == BASE_URL, "Should navigate to home"

    logger.info("✓ Breadcrumb navigation test passed!")
    return True


async def run_all_tests():
    """Run all document management tests."""
    async with async_playwright() as p:
        # Launch browser with persistent context
        logger.info("Launching browser...")

        # Create a user temp directory for playwright
        temp_dir = tempfile.mkdtemp(prefix="playwright_", dir=os.path.expanduser("~"))
        logger.info(f"Using temp directory: {temp_dir}")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=temp_dir,
            headless=False,  # Set to True for headless testing
        )
        page = await context.new_page()

        test_results = {}

        try:
            # Run all tests
            tests = [
                ("Document List Page", test_document_list_page),
                ("Document Upload Page", test_document_upload_page),
                ("Bulk Upload Page", test_bulk_upload_page),
                ("Submissions Page", test_submissions_page),
                ("Email Import Page", test_email_import_page),
                ("Navigation from Navbar", test_navigation_from_navbar),
                ("Document Filter Functionality", test_document_filter_functionality),
                ("Breadcrumb Navigation", test_breadcrumb_navigation),
            ]

            for test_name, test_func in tests:
                try:
                    result = await test_func(page)
                    test_results[test_name] = "PASSED" if result else "FAILED"
                except Exception as e:
                    logger.error(f"Error in {test_name}: {e}")
                    test_results[test_name] = f"ERROR: {str(e)}"
                    # Take screenshot on error
                    screenshot_name = f"error_{test_name.replace(' ', '_').lower()}.png"
                    await page.screenshot(path=screenshot_name)
                    logger.info(f"Screenshot saved to {screenshot_name}")

                # Small delay between tests
                await page.wait_for_timeout(500)

            # Print summary
            logger.info("=" * 60)
            logger.info("TEST SUMMARY")
            logger.info("=" * 60)
            passed = 0
            failed = 0
            for test_name, result in test_results.items():
                status_icon = "✓" if result == "PASSED" else "✗"
                logger.info(f"{status_icon} {test_name}: {result}")
                if result == "PASSED":
                    passed += 1
                else:
                    failed += 1

            logger.info("-" * 60)
            logger.info(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
            logger.info("=" * 60)

            # Wait to see final state
            logger.info("Waiting 3 seconds before closing...")
            await page.wait_for_timeout(3000)

        except Exception as e:
            logger.error(f"Error during tests: {e}")
            await page.screenshot(path="error_screenshot.png")
            logger.info("Screenshot saved to error_screenshot.png")
            raise

        finally:
            await context.close()
            logger.info("Browser closed")

        return test_results


async def main():
    """Main entry point."""
    logger.info("Starting Document Management web interface tests...")
    logger.info(f"Testing against: {BASE_URL}")
    logger.info("")

    results = await run_all_tests()

    # Return exit code based on results
    if all(r == "PASSED" for r in results.values()):
        logger.info("\nAll tests passed!")
        return 0
    logger.error("\nSome tests failed!")
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
