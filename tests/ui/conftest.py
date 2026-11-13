"""
Pytest fixtures for Playwright UI tests.

Auto-starts/stops a Flask dev server for the test session.
"""

import os
import signal
import subprocess
import time

import pytest


@pytest.fixture(scope="session")
def flask_server():
    """Start a Flask dev server for the session and stop it afterwards."""
    port = 5000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    # Disable CSRF in dev for UI tests
    env = os.environ.copy()
    env["WTF_CSRF_ENABLED"] = "False"

    proc = subprocess.Popen(
        [
            "uv", "run", "flask", "--app", "app", "run",
            f"--host={host}",
            f"--port={port}",
            "--no-reload",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for server to be ready
    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen(f"{url}/auth/login")
            break
        except Exception:
            time.sleep(0.3)
    else:
        proc.kill()
        pytest.skip("Flask server did not start in time")

    yield url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
