# Dozentenmanager

Ein umfassendes Verwaltungssystem für Hochschuldozenten zur Organisation von Studierenden, Lehrveranstaltungen, Prüfungen und Bewertungen über mehrere Institutionen hinweg.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 219 passing](https://img.shields.io/badge/tests-219%20passing-success.svg)](tests/)

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Technologie-Stack](#-technologie-stack)
- [Installation](#-installation)
- [Verwendung](#-verwendung)
- [Entwicklung](#-entwicklung)
- [Projekt-Struktur](#-projekt-struktur)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Mitwirken](#-mitwirken)

## ✨ Features

### Phase 1 - Kernfunktionen (✅ Abgeschlossen - v0.5.0)

#### 🏛️ Universitätsverwaltung
- CRUD-Operationen für Universitäten
- Automatische Slug-Generierung für URL-freundliche Identifikatoren
- Unterstützung für deutsche Umlaute
- Suchfunktion nach Universitätsname
- CLI und Web-Interface

#### 👨‍🎓 Studierendenverwaltung
- Vollständige Verwaltung von Studierendendaten
- E-Mail-Validierung (Format-Prüfung)
- Matrikelnummer-Validierung (8 Ziffern)
- Such- und Filterfunktionen (Name, Matrikelnummer, E-Mail, Studiengang)
- CLI und Web-Interface

#### 📚 Lehrveranstaltungsverwaltung
- Verwaltung von Kursen mit Semester-Zuordnung
- Semester-Format-Validierung (YYYY_SoSe / YYYY_WiSe)
- Automatische Slug-Generierung
- Verknüpfung mit Universitäten
- Filter nach Universität und Semester
- CLI und Web-Interface

#### 📝 Einschreibungsverwaltung
- Student-Kurs-Zuordnung (Many-to-Many Beziehung)
- Status-Tracking (aktiv, abgeschlossen, abgebrochen)
- Automatische Datumsverwaltung (Einschreibung/Abmeldung)
- Schutz vor Doppel-Einschreibungen
- Interaktive Modal-Dialoge für Einschreibung
- CLI und Web-Interface

#### 📊 Prüfungsverwaltung
- CRUD-Operationen für Prüfungen und Assessments
- Prüfungstermin-Verwaltung
- Punkteverwaltung (maximale Punktzahl)
- Gewichtung für Gesamtnote (0-100%)
- Verknüpfung mit Lehrveranstaltungen
- CLI und Web-Interface

### 🔮 Geplante Features (Phase 2+)

- Dokumenten-Management (PDF-Upload und Organisation)
- Bewertungssystem (Noten- und Punkteeingabe für Prüfungen)
- Statistiken und Berichte
- Export-Funktionen (CSV, PDF)
- E-Mail-Benachrichtigungen
- Audit-Trail für alle Änderungen

## 🛠️ Technologie-Stack

### Backend
- **Python 3.12+** - Programmiersprache
- **Flask 3.0+** - Web-Framework
- **SQLAlchemy** - ORM für Datenbank-Zugriffe
- **Alembic** - Datenbank-Migrationen
- **SQLite** - Datenbank (entwicklung)

### Frontend
- **Jinja2** - Template-Engine
- **Bulma CSS** - Responsive CSS-Framework
- **JavaScript** - Client-seitige Interaktivität

### Entwicklungswerkzeuge
- **UV** - Schneller Python-Paketmanager
- **Ruff** - Linting und Formatierung
- **mypy** - Statische Typ-Prüfung
- **pytest** - Test-Framework
- **Playwright** - Browser-Automatisierung für E2E-Tests
- **pre-commit** - Git-Hooks für Code-Qualität

## 📦 Installation

### Voraussetzungen

- Python 3.12 oder höher
- UV Paketmanager ([Installation](https://github.com/astral-sh/uv))
- Git

### Schritt-für-Schritt Anleitung

1. **Repository klonen**
   ```bash
   git clone https://github.com/jvanvinkenroye/dozentenmanager.git
   cd dozentenmanager
   ```

2. **Virtuelle Umgebung erstellen**
   ```bash
   uv venv --seed
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Abhängigkeiten installieren**
   ```bash
   uv sync
   ```

4. **Umgebungsvariablen konfigurieren**
   ```bash
   cp .env.example .env
   # .env bearbeiten und anpassen
   ```

5. **Datenbank initialisieren**
   ```bash
   alembic upgrade head
   ```

6. **Pre-commit Hooks installieren** (optional, empfohlen)
   ```bash
   pre-commit install
   ```

7. **Anwendung starten**
   ```bash
   python run.py
   ```

Die Anwendung ist jetzt unter `http://127.0.0.1:5009` erreichbar.

### 🐳 Docker Installation (Alternative)

Für eine einfachere Bereitstellung können Sie Docker verwenden:

```bash
# Development: Mit Docker Compose starten
docker-compose up -d

# Datenbank initialisieren
docker-compose exec web alembic upgrade head

# Anwendung ist verfügbar unter http://localhost:5000
```

**Produktions-Deployment:**
```bash
# Produktions-Image bauen und starten
docker-compose -f docker-compose.prod.yml up -d
```

Für detaillierte Docker-Anweisungen siehe [DOCKER.md](DOCKER.md).

## 🚀 Verwendung

### Web-Interface

Nach dem Start der Anwendung mit `python run.py` können Sie das Web-Interface unter `http://127.0.0.1:5009` nutzen.

**Verfügbare Funktionen:**
- `/` - Startseite mit Übersicht
- `/universities` - Universitätsverwaltung
- `/students` - Studierendenverwaltung
- `/courses` - Lehrveranstaltungsverwaltung
- `/courses/<id>` - Kursdetails mit Einschreibungsverwaltung
- `/exams` - Prüfungsverwaltung

### CLI-Tools

Alle Funktionen sind auch über die Kommandozeile verfügbar:

#### Universitäten verwalten
```bash
# Universität hinzufügen
python cli/university_cli.py add --name "TH Köln" --location "Köln"

# Universitäten auflisten
python cli/university_cli.py list

# Universität anzeigen
python cli/university_cli.py show --slug th-koeln
```

#### Studierende verwalten
```bash
# Studierenden hinzufügen
python cli/student_cli.py add \
  --first-name Max \
  --last-name Mustermann \
  --student-id 12345678 \
  --email max.mustermann@example.com \
  --program "Informatik"

# Studierende auflisten
python cli/student_cli.py list

# Nach Studiengang filtern
python cli/student_cli.py list --program "Informatik"
```

#### Lehrveranstaltungen verwalten
```bash
# Kurs hinzufügen
python cli/course_cli.py add \
  --name "Einführung in die Statistik" \
  --code "STAT-101" \
  --semester "2024_WiSe" \
  --credits 5 \
  --university-id 1

# Kurse auflisten
python cli/course_cli.py list

# Nach Semester filtern
python cli/course_cli.py list --semester "2024_WiSe"
```

#### Einschreibungen verwalten
```bash
# Studierenden einschreiben
python cli/enrollment_cli.py add --student-id 1 --course-id 1

# Einschreibungen anzeigen
python cli/enrollment_cli.py list --course-id 1

# Status aktualisieren
python cli/enrollment_cli.py update-status \
  --student-id 1 \
  --course-id 1 \
  --status completed
```

#### Prüfungen verwalten
```bash
# Prüfung hinzufügen
python cli/exam_cli.py add \
  --name "Klausur Statistik I" \
  --course-id 1 \
  --exam-date 2024-06-15 \
  --max-points 100 \
  --weight 60

# Prüfungen auflisten
python cli/exam_cli.py list

# Nach Kurs filtern
python cli/exam_cli.py list --course-id 1

# Prüfung aktualisieren
python cli/exam_cli.py update --id 1 --max-points 120
```

Alle CLI-Tools unterstützen `--help` für detaillierte Informationen:
```bash
python cli/student_cli.py --help
```

## 👨‍💻 Entwicklung

### Entwicklungs-Workflow

Dieses Projekt folgt einem **CLI-First Workflow**:

1. CLI-Funktionalität implementieren (`cli/`)
2. Unit-Tests schreiben (`tests/unit/`)
3. Linting und Type-Checking durchführen
4. CLI-Implementation committen
5. Flask-Routes implementieren (`app/routes/`)
6. Integration-Tests schreiben (`tests/integration/`)
7. Flask-Integration committen

### Code-Qualität sicherstellen

```bash
# Formatierung und Linting
ruff check --fix .
ruff format .

# Type-Checking
mypy app/ cli/

# Tests ausführen
pytest

# Tests mit Coverage
pytest --cov=app --cov=cli --cov-report=html
```

### Datenbank-Migrationen

```bash
# Migration erstellen (nach Model-Änderungen)
alembic revision --autogenerate -m "Beschreibung der Änderung"

# Migration überprüfen (im migrations/versions/ Ordner)
# Migration anwenden
alembic upgrade head

# Migration rückgängig machen
alembic downgrade -1
```

### Neue Features hinzufügen

Detaillierte Anleitung in [`/ref/development-workflow.md`](ref/development-workflow.md).

**Zusammenfassung:**
1. CLI-Tool in `cli/` erstellen
2. Tests in `tests/unit/` schreiben
3. Flask-Route in `app/routes/` erstellen
4. Templates in `app/templates/` erstellen
5. Integration-Tests in `tests/integration/` schreiben
6. Dokumentation aktualisieren

## 📁 Projekt-Struktur

```
dozentenmanager/
├── app/                        # Flask-Anwendung
│   ├── __init__.py            # Application Factory
│   ├── models/                # Datenbank-Modelle
│   │   ├── university.py
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   └── exam.py
│   ├── routes/                # Flask Blueprints
│   │   ├── university.py
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   └── exam.py
│   ├── templates/             # Jinja2 Templates
│   │   ├── base.html
│   │   ├── university/
│   │   ├── student/
│   │   ├── course/
│   │   ├── enrollment/
│   │   └── exam/
│   └── static/                # CSS, JavaScript, Bilder
│       └── css/
├── cli/                       # CLI-Tools
│   ├── university_cli.py
│   ├── student_cli.py
│   ├── course_cli.py
│   ├── enrollment_cli.py
│   └── exam_cli.py
├── tests/                     # Test-Suite
│   ├── unit/                  # Unit-Tests
│   ├── integration/           # Integration-Tests
│   └── fixtures/              # Test-Daten
├── migrations/                # Alembic-Migrationen
├── uploads/                   # Hochgeladene Dateien
├── ref/                       # Referenz-Dokumentation
│   ├── project-overview.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── development-workflow.md
│   └── features.md
├── config.py                  # Konfiguration
├── run.py                     # Anwendungs-Einstiegspunkt
├── pyproject.toml             # Projekt-Abhängigkeiten
├── .env.example               # Umgebungsvariablen-Vorlage
├── CHANGELOG.md               # Änderungsprotokoll
├── CLAUDE.md                  # Projekt-Richtlinien
└── README.md                  # Diese Datei
```

## 🧪 Testing

### Test-Suite ausführen

```bash
# Alle Tests
pytest

# Mit Verbose-Output
pytest -v

# Nur Unit-Tests
pytest tests/unit/

# Nur Integration-Tests
pytest tests/integration/

# Mit Coverage-Report
pytest --cov=app --cov=cli --cov-report=html
open htmlcov/index.html  # macOS
```

### Test-Statistiken

**v0.5.0:**
- **219 Tests** (175 Unit + 44 Integration)
- **100% Pass-Rate**
- **Coverage:** Umfassende Abdeckung aller CRUD-Operationen
- **E2E-Tests:** Playwright Browser-Automatisierung

### Testing-Kategorien

- **Unit-Tests:** Testen CLI-Funktionen isoliert
- **Integration-Tests:** Testen Flask-Routes mit Datenbank
- **E2E-Tests:** Vollständige Workflows im Browser

## 🗺️ Roadmap

### ✅ Phase 1: Kern-Datenverwaltung (Abgeschlossen - v0.5.0)
- [x] 1.1 Universitätsverwaltung
- [x] 1.2 Studierendenverwaltung
- [x] 1.3 Lehrveranstaltungsverwaltung
- [x] 1.4 Einschreibungsverwaltung
- [x] 1.5 Prüfungsverwaltung (Struktur und CRUD)

### 🚧 Phase 2: Dokumenten-Management (Geplant)
- [ ] 2.1 Datei-Upload-System
- [ ] 2.2 Dokumenten-Organisation
- [ ] 2.3 PDF-Viewer-Integration
- [ ] 2.4 Volltextsuche

### 📋 Phase 3: Bewertungssystem (Geplant)
- [ ] 3.1 Bewertungseingabe (Punkte/Noten pro Prüfung)
- [ ] 3.2 Notenspiegel und Übersichten
- [ ] 3.3 Statistiken und Analysen
- [ ] 3.4 Automatische Notenberechnung

### 📊 Phase 4: Erweiterte Features (Geplant)
- [ ] 4.1 E-Mail-Benachrichtigungen
- [ ] 4.2 Export-Funktionen (CSV, PDF)
- [ ] 4.3 Audit-Trail
- [ ] 4.4 Multi-User-Support mit Rollen

Detaillierte Feature-Beschreibungen in [`/ref/features.md`](ref/features.md).

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte beachten Sie:

1. **Code-Qualität:** Alle Code-Änderungen müssen Linting (ruff) und Type-Checking (mypy) bestehen
2. **Tests:** Neue Features benötigen Unit- und Integration-Tests
3. **CLI-First:** Implementieren Sie zuerst CLI-Funktionalität, dann Web-Interface
4. **Dokumentation:** Aktualisieren Sie relevante Dokumentation

### Entwicklungs-Richtlinien

- Python 3.12+ erforderlich
- Folgen Sie PEP 8 Coding-Standards
- Schreiben Sie aussagekräftige Commit-Messages (Conventional Commits)
- Docstrings für alle Funktionen und Klassen
- Type Hints erforderlich
- Deutsche Sprache für Web-Interface, Englisch für Code/Kommentare

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

## 📞 Kontakt

Bei Fragen oder Anregungen können Sie ein Issue auf GitHub erstellen oder einen Pull Request einreichen.

---

**Dozentenmanager** - Vereinfachen Sie Ihre Lehrverwaltung.

*Entwickelt mit ❤️ und Python*
