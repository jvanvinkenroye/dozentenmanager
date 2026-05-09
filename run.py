"""
Application entry point for Dozentenmanager.

This module creates the Flask application instance and runs the development server.
Use this file to run the application:
    python run.py
    or
    flask run
"""

import os

from app import create_app

app = create_app()


def main() -> None:
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
