"""
Test enrollment web interface using Playwright.

This script demonstrates the enrollment functionality by:
1. Opening the course detail page
2. Verifying existing enrollments
3. Enrolling a new student via the modal form
4. Verifying the enrollment was successful
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5002"


async def test_enrollment():
    """Test the enrollment web interface."""
    async with async_playwright() as p:
        # Launch browser with persistent context
        logger.info("Launching browser...")
        import tempfile
        import os

        # Create a user temp directory for playwright
        temp_dir = tempfile.mkdtemp(prefix="playwright_", dir=os.path.expanduser("~"))
        logger.info(f"Using temp directory: {temp_dir}")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=temp_dir,
            headless=False  # Set to False to see the browser
        )
        page = await context.new_page()

        try:
            # Navigate to course detail page
            logger.info("Opening course detail page...")
            await page.goto(f"{BASE_URL}/courses/1")
            await page.wait_for_load_state("networkidle")

            # Verify page title
            title = await page.title()
            logger.info(f"Page title: {title}")

            # Check current enrollments
            logger.info("Checking current enrollments...")
            enrollment_rows = await page.locator("table tbody tr").count()
            logger.info(f"Current enrollments: {enrollment_rows}")

            # Get student names from enrollment table
            for i in range(enrollment_rows):
                student_name = await page.locator(f"table tbody tr:nth-child({i+1}) td:nth-child(1)").text_content()
                student_id = await page.locator(f"table tbody tr:nth-child({i+1}) td:nth-child(2)").text_content()
                status = await page.locator(f"table tbody tr:nth-child({i+1}) td:nth-child(3)").text_content()
                logger.info(f"  - {student_name.strip()} (ID: {student_id.strip()}) - Status: {status.strip()}")

            # Click "Einschreiben" button to open modal
            logger.info("Opening enrollment modal...")
            await page.click("button:has-text('Einschreiben')")
            await page.wait_for_selector(".modal.is-active", timeout=2000)
            logger.info("Modal opened")

            # Select Lisa Weber from dropdown
            logger.info("Selecting Lisa Weber from dropdown...")
            await page.select_option("select[name='student_id']", label="Weber, Lisa (33333333)")

            # Submit the form
            logger.info("Submitting enrollment form...")
            await page.click("button[type='submit']:has-text('Einschreiben')")

            # Wait for page reload and success message
            await page.wait_for_load_state("networkidle")

            # Check for success flash message
            flash_message = await page.locator(".notification.is-success, .message.is-success").text_content()
            logger.info(f"Success message: {flash_message.strip()}")

            # Verify new enrollment count
            new_enrollment_rows = await page.locator("table tbody tr").count()
            logger.info(f"Enrollments after adding Lisa: {new_enrollment_rows}")

            if new_enrollment_rows == enrollment_rows + 1:
                logger.info("✓ Enrollment successful! Lisa Weber was added.")
            else:
                logger.error(f"✗ Expected {enrollment_rows + 1} enrollments, but found {new_enrollment_rows}")

            # List all current enrollments
            logger.info("Current enrollments after adding Lisa:")
            for i in range(new_enrollment_rows):
                student_name = await page.locator(f"table tbody tr:nth-child({i+1}) td:nth-child(1)").text_content()
                student_id = await page.locator(f"table tbody tr:nth-child({i+1}) td:nth-child(2)").text_content()
                status = await page.locator(f"table tbody tr:nth-child({i+1}) td:nth-child(3)").text_content()
                logger.info(f"  - {student_name.strip()} (ID: {student_id.strip()}) - Status: {status.strip()}")

            # Wait a bit to see the final state
            logger.info("Waiting 3 seconds to view the result...")
            await page.wait_for_timeout(3000)

            # Test unenrollment
            logger.info("Testing unenrollment by removing the first student...")

            # Handle the confirmation dialog
            page.on("dialog", lambda dialog: dialog.accept())

            # Click the first delete button
            await page.click("table tbody tr:nth-child(1) button.is-danger")

            # Wait for page reload
            await page.wait_for_load_state("networkidle")

            # Check flash message
            flash_message = await page.locator(".notification.is-success, .message.is-success").text_content()
            logger.info(f"Unenrollment message: {flash_message.strip()}")

            # Verify enrollment count decreased
            final_enrollment_rows = await page.locator("table tbody tr").count()
            logger.info(f"Final enrollment count: {final_enrollment_rows}")

            if final_enrollment_rows == new_enrollment_rows - 1:
                logger.info("✓ Unenrollment successful!")
            else:
                logger.error(f"✗ Expected {new_enrollment_rows - 1} enrollments, but found {final_enrollment_rows}")

            # Wait to see final result
            logger.info("Waiting 3 seconds before closing...")
            await page.wait_for_timeout(3000)

        except Exception as e:
            logger.error(f"Error during test: {e}")
            # Take screenshot on error
            await page.screenshot(path="error_screenshot.png")
            logger.info("Screenshot saved to error_screenshot.png")
            raise

        finally:
            await context.close()
            logger.info("Browser closed")


async def main():
    """Main entry point."""
    logger.info("Starting enrollment web interface test...")
    await test_enrollment()
    logger.info("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
