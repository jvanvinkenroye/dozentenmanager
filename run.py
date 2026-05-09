"""
Application entry point for Dozentenmanager.

Usage:
    dozentenmanager          # Start the server
    dozentenmanager init     # Create user config interactively
    dozentenmanager migrate  # Run database migrations
"""

import os
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "dozentenmanager"
CONFIG_FILE = CONFIG_DIR / "config.env"


def _prompt(label: str, default: str = "", secret: bool = False) -> str:
    hint = f" [{default}]" if default else ""
    if secret:
        import getpass

        value = getpass.getpass(f"{label}{hint}: ")
    else:
        value = input(f"{label}{hint}: ").strip()
    return value or default


def cmd_init() -> None:
    """Interactively create ~/.config/dozentenmanager/config.env."""
    print("Dozentenmanager - Erstkonfiguration")
    print("=" * 40)

    if CONFIG_FILE.exists():
        answer = input(
            f"Config existiert bereits ({CONFIG_FILE}). Überschreiben? [j/N] "
        )
        if answer.strip().lower() not in ("j", "ja", "y", "yes"):
            print("Abgebrochen.")
            return

    import secrets

    secret_key = secrets.token_hex(32)
    db_default = str(
        Path.home() / ".local" / "share" / "dozentenmanager" / "dozentenmanager.db"
    )

    print("\nDatenbankpfad (absoluter Pfad zur SQLite-Datei):")
    db_path = _prompt("  Pfad", db_default)

    print("\nAdmin-User (leer lassen zum Überspringen):")
    admin_username = _prompt("  Benutzername", "admin")
    admin_email = _prompt("  E-Mail", "admin@localhost")
    admin_password = _prompt("  Passwort", secret=True)

    print("\nServer:")
    port = _prompt("  Port", "5000")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dozentenmanager Konfiguration",
        f"SECRET_KEY={secret_key}",
        f"DATABASE_URL=sqlite:///{db_path}",
        f"PORT={port}",
        "FLASK_ENV=production",
        "LOG_LEVEL=INFO",
    ]
    if admin_username and admin_password:
        lines += [
            f"ADMIN_USERNAME={admin_username}",
            f"ADMIN_EMAIL={admin_email}",
            f"ADMIN_PASSWORD={admin_password}",
        ]

    CONFIG_FILE.write_text("\n".join(lines) + "\n")
    CONFIG_FILE.chmod(0o600)

    print(f"\nConfig gespeichert: {CONFIG_FILE}")
    print("Starte jetzt mit: dozentenmanager migrate && dozentenmanager")


def cmd_migrate() -> None:
    """Run database migrations (flask db upgrade)."""
    from flask_migrate import upgrade

    from app import create_app

    app = create_app()
    with app.app_context():
        upgrade()
    print("Migrationen erfolgreich angewendet.")


def cmd_serve() -> None:
    """Start the web server."""
    from app import create_app

    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "serve"
    commands = {
        "init": cmd_init,
        "migrate": cmd_migrate,
        "serve": cmd_serve,
    }
    if command not in commands:
        print(f"Unbekannter Befehl: {command}")
        print(f"Verfügbar: {', '.join(commands)}")
        sys.exit(1)
    commands[command]()


# Flask requires a top-level `app` for `flask` CLI compatibility
def _get_app():
    from app import create_app

    return create_app()


app = _get_app()

if __name__ == "__main__":
    main()
