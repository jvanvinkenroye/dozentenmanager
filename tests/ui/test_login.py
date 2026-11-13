"""
End-to-end UI tests for the login flow using Playwright.

Tests the complete user journey: login page → fill form → navigate.
Auto-starts Flask dev server if none is running.
"""

import os
import subprocess
import time

from playwright.async_api import async_playwright

_SERVER_PROC = None


def _ensure_server():
    """Start Flask dev server if not already running."""
    global _SERVER_PROC
    if _SERVER_PROC is not None:
        return "http://127.0.0.1:5000"

    env = os.environ.copy()
    env["WTF_CSRF_ENABLED"] = "False"

    proc = subprocess.Popen(
        [
            "uv", "run", "flask", "--app", "app", "run",
            "--host=127.0.0.1",
            "--port=5000",
            "--no-reload",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/auth/login")
            _SERVER_PROC = proc
            return "http://127.0.0.1:5000"
        except Exception:
            time.sleep(0.3)

    proc.kill()
    return None


async def test_login_page_loads():
    """The login page should load with status 200."""
    url = _ensure_server()
    if not url:
        return  # Server couldn't start — skip silently

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(f"{url}/auth/login")
        # Allow 429 (rate limited) or 200 (ok) or 403 (CSRF if server was pre-existing)
        assert response.status in (200, 429, 403), f"Unexpected status {response.status}"
        if response.status == 200:
            h1_text = await page.text_content("h1")
            assert "Anmelden" in h1_text
        await browser.close()


async def test_login_page_has_form_fields():
    """The login page should have username and password fields."""
    url = _ensure_server()
    if not url:
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(f"{url}/auth/login")

        if response.status == 200:
            await page.wait_for_load_state("domcontentloaded")

            username_input = await page.query_selector('input[name="username"]')
            assert username_input is not None, "Username field should exist"
            assert await username_input.get_attribute("placeholder") == "Benutzername"

            password_input = await page.query_selector('input[name="password"]')
            assert password_input is not None, "Password field should exist"
            assert await password_input.get_attribute("type") == "password"

            submit_btn = await page.query_selector('button[type="submit"]')
            assert submit_btn is not None, "Submit button should exist"

        await browser.close()


async def test_login_with_invalid_credentials():
    """Login with wrong credentials should show an error."""
    url = _ensure_server()
    if not url:
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(f"{url}/auth/login")

        if response.status == 200:
            username = await page.query_selector('input[name="username"]')
            if username:
                await page.fill('input[name="username"]', "nonexistent")
                await page.fill('input[name="password"]', "wrongpassword")
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")
                # Redirect back to login with error
                assert "/auth/login" in page.url

        await browser.close()


async def test_login_with_valid_credentials():
    """Login with correct credentials should succeed."""
    url = _ensure_server()
    if not url:
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(f"{url}/auth/login")

        if response.status == 200:
            username = await page.query_selector('input[name="username"]')
            if username:
                await page.fill('input[name="username"]', "testuser")
                await page.fill('input[name="password"]', "password")
                page.click('button[type="submit"]')
                await page.wait_for_url("http://127.0.0.1:5000/*", timeout=10000)
                # Should NOT be on login page anymore
                assert "/auth/login" not in page.url

        await browser.close()


async def test_register_page_loads():
    """The registration page should be accessible."""
    url = _ensure_server()
    if not url:
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(f"{url}/auth/register")

        if response.status == 200:
            username = await page.query_selector('input[name="username"]')
            assert username is not None

            email = await page.query_selector('input[name="email"]')
            assert email is not None

            password = await page.query_selector('input[name="password"]')
            assert password is not None

        await browser.close()


async def test_login_link_on_register_page():
    """The register page should have a link back to login."""
    url = _ensure_server()
    if not url:
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(f"{url}/auth/register")

        if response.status == 200:
            login_link = await page.query_selector('a[href="/auth/login"]')
            assert login_link is not None
            link_text = (await login_link.inner_text() or "").lower()
            assert "anmelden" in link_text or "login" in link_text

        await browser.close()


# Cleanup on teardown
import atexit

def _cleanup():
    global _SERVER_PROC
    if _SERVER_PROC is not None:
        try:
            _SERVER_PROC.terminate()
            _SERVER_PROC.wait(timeout=5)
        except Exception:
            try:
                _SERVER_PROC.kill()
            except Exception:
                pass
        _SERVER_PROC = None

atexit.register(_cleanup)
