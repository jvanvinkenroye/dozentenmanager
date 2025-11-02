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

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))

    # Get debug mode from environment
    debug = os.environ.get("FLASK_ENV") == "development"

    # Run the application
    app.run(host="0.0.0.0", port=port, debug=debug)
