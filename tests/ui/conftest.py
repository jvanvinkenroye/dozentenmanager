"""
Pytest fixtures for Playwright UI tests.

Provides a running Flask test server and browser context.
"""

import pytest


@pytest.fixture(scope="session")
def browser_context_args():
    """Configure Playwright browser context for tests."""
    return {"headless": True}
