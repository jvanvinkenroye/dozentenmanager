# Dozentenmanager

Verwaltungssystem für Hochschuldozenten zur Organisation von Studierenden, Lehrveranstaltungen, Prüfungen und Benotung über mehrere Institutionen hinweg.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)

---

## Inhaltsverzeichnis

- [Features](#features)
- [Architekturübersicht](#architekturübersicht)
- [Installation](#installation)
- [CLI-Tool](#cli-tool)
- [Docker / Podman](#docker--podman)
- [Entwicklung](#entwicklung)

---

## Features

| Bereich | Funktion |
|---|---|
| Authentifizierung | Login/Logout, Rollen (admin/user), CSRF-Schutz |
| Universitäten | CRUD, automatische Slug-Generierung |
| Studierende | CRUD, CSV/XLSX-Import, Such- und Filterfunktionen |
| Lehrveranstaltungen | CRUD, Semester-Verwaltung, Einschreibungsübersicht |
| Einschreibungen | Student-Kurs-Zuordnung, Status-Tracking |
| Prüfungen | CRUD, Punkteverwaltung, Gewichtung |
| Benotung | Noteneingabe, automatische Notenberechnung (deutsche Skala), Notenspiegel |
| Statistiken | Notenverteilung, Bestehensquote, Durchschnitt, Einzelstudent-Übersicht |
| Dokumente | Datei-Upload, automatische Ordnerstruktur, E-Mail-Import (.eml) |
| Backup | Vollständiger Datenexport |
| Audit-Log | Nachvollziehbarkeit aller Änderungen (Admin) |

---

## Architekturübersicht

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser / Client                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────────┐
│                    Flask (Blueprints)                        │
│                                                             │
│  /auth   /students  /courses  /exams  /grades  /statistics  │
│  /universities  /enrollments  /documents  /backup  /admin   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Service Layer                             │
│                                                             │
│  StudentService  CourseService  EnrollmentService           │
│  ExamService     GradeService   UniversityService           │
│  AuditService    StatisticsService                          │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQLAlchemy ORM
┌─────────────────────▼───────────────────────────────────────┐
│                    Datenbank (SQLite)                        │
│                                                             │
│  university  student  course  enrollment  exam              │
│  grade  grade_threshold  grading_scale                      │
│  document  submission  audit_log  user                      │
└─────────────────────────────────────────────────────────────┘
```

### Verzeichnisstruktur

```
dozentenmanager/
├── app/
│   ├── __init__.py          # Application Factory (create_app)
│   ├── models/              # SQLAlchemy-Modelle
│   │   ├── university.py
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   ├── exam.py
│   │   ├── grade.py         # Grade, GradingScale, GradeThreshold
│   │   ├── document.py
│   │   └── user.py
│   ├── services/            # Business Logic
│   │   ├── base_service.py
│   │   ├── student_service.py
│   │   ├── course_service.py
│   │   ├── enrollment_service.py
│   │   ├── exam_service.py
│   │   ├── grade_service.py
│   │   ├── university_service.py
│   │   ├── audit_service.py
│   │   └── statistics_service.py
│   ├── routes/              # Flask Blueprints
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   ├── exam.py
│   │   ├── grade.py
│   │   ├── statistics.py
│   │   ├── document.py
│   │   ├── university.py
│   │   ├── backup.py
│   │   ├── admin.py
│   │   └── api.py
│   ├── forms/               # WTForms
│   ├── utils/               # Hilfsfunktionen
│   ├── templates/           # Jinja2-Templates (Bulma CSS)
│   └── static/              # CSS, JavaScript
├── cli/                     # Standalone CLI-Tools (Typer/Click)
├── migrations/              # Alembic-Migrationen
├── tests/
│   ├── unit/
│   └── integration/
├── config.py                # Konfigurationsklassen
├── run.py                   # Einstiegspunkt + CLI (init/serve)
└── pyproject.toml
```

### Datenbankschema (vereinfacht)

```
university ──< course ──< exam ──< grade
                │                   │
                └──< enrollment >───┘
                         │
                      student

user (eigenständig, für Login)
audit_log (eigenständig, protokolliert alle Änderungen)
document / submission (eigenständig, verknüpft mit enrollment)
```

### Schichtenmodell

| Schicht | Verantwortung |
|---|---|
| **Routes** (Blueprints) | HTTP-Request/Response, Flash-Messages, Redirect |
| **Services** | Business-Logik, Validierung, Fehlerbehandlung (Exceptions) |
| **Models** | Datenbankstruktur, Relationen, einfache Berechnungen |
| **Templates** | Darstellung, Bulma CSS, Chart.js für Statistiken |

Services werfen `ValueError` / `IntegrityError` — Routes fangen diese und zeigen sie als Flash-Messages an.

---

## Datenspeicherung

Alle Daten liegen **außerhalb des Projektverzeichnisses** (kein Datenverlust beim Löschen/Update des Repos):

| Datei/Ordner | Pfad | Inhalt |
|---|---|---|
| Konfiguration | `~/.config/dozentenmanager/config.env` | SECRET_KEY, PORT, ADMIN_*, DATABASE_URL |
| Datenbank | `~/.local/share/dozentenmanager/dozentenmanager.db` | Alle App-Daten (SQLite) |
| Uploads | `./uploads/` (relativ zum Startverzeichnis) | Hochgeladene Dateien |
| Logs | `./logs/dozentenmanager.log` | Anwendungslog (max. 10 MB × 10 Dateien) |

> **Tipp:** `DATABASE_URL` in `config.env` auf einen anderen Pfad setzen, um die Datenbank zu verschieben.
> Für Docker/Podman werden `instance/` und `uploads/` als Volumes eingehängt (siehe `docker-compose.yml`).

---

## Installation

### Voraussetzungen

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) (`pip install uv` oder `brew install uv`)

### Als installiertes CLI-Tool (empfohlen)

```bash
# Installieren
uv tool install git+https://github.com/jvanvinkenroye/dozentenmanager.git

# Oder aus lokalem Verzeichnis
uv tool install .

# Einmalige Konfiguration
dozentenmanager init

# Starten
dozentenmanager
```

### Für Entwicklung

```bash
git clone https://github.com/jvanvinkenroye/dozentenmanager.git
cd dozentenmanager

uv venv --seed
source .venv/bin/activate

uv sync

cp .env.example .env
# .env anpassen (SECRET_KEY, optional ADMIN_*)

uv run python run.py
```

Die App läuft auf `http://localhost:5000`.

### Admin-User anlegen

Entweder über `dozentenmanager init` (interaktiv) oder manuell in `~/.config/dozentenmanager/config.env` / `.env`:

```env
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=sicheres-passwort
```

Der User wird beim nächsten Start automatisch erstellt.

---

## CLI-Tool

```
dozentenmanager [Befehl]

Befehle:
  (kein Befehl)   Startet den Webserver
  init            Interaktive Erstkonfiguration (~/.config/dozentenmanager/config.env)
  serve           Startet den Webserver (explizit)
```

### Konfiguration

Die Konfiguration wird in dieser Reihenfolge geladen (spätere überschreiben frühere):

1. `~/.config/dozentenmanager/config.env` — Benutzerkonfiguration
2. `.env` im Projektverzeichnis — lokale Entwicklung

| Variable | Standard | Beschreibung |
|---|---|---|
| `SECRET_KEY` | — (Pflicht) | Flask-Session-Schlüssel |
| `DATABASE_URL` | `~/.local/share/dozentenmanager/dozentenmanager.db` | SQLite-Pfad |
| `PORT` | `5000` | Serverport |
| `FLASK_ENV` | `production` | `development` aktiviert Debug-Modus |
| `ADMIN_USERNAME` | — | Admin-User beim ersten Start anlegen |
| `ADMIN_EMAIL` | — | Admin-E-Mail |
| `ADMIN_PASSWORD` | — | Admin-Passwort |

### Standalone CLI-Tools (`cli/`)

Für Skripte und Automatisierung stehen direkte CLI-Tools zur Verfügung:

```bash
# Studierende
uv run python cli/student_cli.py add --first-name Max --last-name Muster --student-id 12345678 --email m@example.com --program Informatik
uv run python cli/student_cli.py list
uv run python cli/student_cli.py import --file studis.csv --on-duplicate skip

# Universitäten
uv run python cli/university_cli.py add --name "TH Köln" --location Köln
uv run python cli/university_cli.py list

# Lehrveranstaltungen
uv run python cli/course_cli.py add --name "Statistik I" --semester 2024_WiSe --university-id 1

# Prüfungen
uv run python cli/exam_cli.py add --name "Klausur" --course-id 1 --exam-date 2024-06-15 --max-points 100

# Noten
uv run python cli/grade_cli.py add --enrollment-id 1 --exam-id 1 --points 78
```

Jedes Tool unterstützt `--help`.

---

## Docker / Podman

### Entwicklung

```bash
docker compose up --build
# Podman:
podman-compose up --build
```

App läuft auf `http://localhost:5001`.
Source-Code wird live eingehängt (Änderungen ohne Neustart sichtbar).

### Produktion

```bash
# .env.docker anlegen
cp .env.example .env.docker
# SECRET_KEY und ADMIN_* setzen

docker compose -f docker-compose.prod.yml up --build -d
```

App läuft auf `http://localhost:8000`, optional Nginx auf `http://localhost:8888`.

Die Datenbank und Uploads werden in Docker-Volumes gespeichert (`dozentenmanager-instance`, `dozentenmanager-uploads`).

---

## Entwicklung

### Code-Qualität

```bash
ruff check --fix .
ruff format .
mypy app/ cli/
pytest
```

### Workflow für neue Features

1. Service in `app/services/` implementieren
2. Unit-Tests in `tests/unit/`
3. Flask-Route in `app/routes/` (nutzt Service)
4. Template in `app/templates/`
5. Integration-Tests in `tests/integration/`

### Migrationen

```bash
# Nach Model-Änderungen
flask db migrate -m "Beschreibung"
flask db upgrade

# Oder automatisch beim Start:
dozentenmanager  # führt Migrationen beim Start aus
```

### Konventionen

- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:` …)
- **Sprache:** Web-Interface auf Deutsch, Code/Kommentare auf Englisch
- **Branches:** Feature-Branches, PR gegen `main`
