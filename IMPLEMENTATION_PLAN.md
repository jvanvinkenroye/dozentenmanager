# Dozentenmanager - Phase 4+5 Implementation Plan

## Übersicht

**Ziel:** Vollständige Umsetzung von Phase 4 (Code Quality) und Phase 5 (Extended Features)

**Geschätzter Aufwand:** 80-100 Stunden

**Authentifizierung:** Session-based mit Flask-Login

---

## Phase 4: Code Quality (~20h)

### 4.1 Test Coverage auf 60% (~15h)

#### 4.1.1 GradeService Unit Tests (5h)
**Datei erstellen:** `tests/unit/test_grade_service.py`

Tests für:
- `add_grade()` - Validierung, Punkte-Berechnung
- `update_grade()` - Update mit Neuberechnung
- `delete_grade()` - Löschen
- `list_grades()` - Filter (enrollment_id, exam_id, course_id, is_final)
- `calculate_weighted_average()` - Gewichtete Durchschnitte
- `get_exam_statistics()` - Min/Max/Avg/Pass-Rate
- `add_exam_component()` - Gewichtsvalidierung
- `create_default_grading_scale()` - Deutsche Notenskala

**Geschätzte Tests:** 20-25

#### 4.1.2 DocumentService Unit Tests (5h)
**Datei erstellen:** `tests/unit/test_document_service.py`

Tests für:
- `get_upload_path()` - Pfadgenerierung
- `create_submission()` - Submission-Erstellung
- `upload_document()` - Datei-Upload mit Validierung
- `list_documents()` - Filter (enrollment, submission, file_type)
- `delete_document()` - Löschen mit Datei
- `update_submission_status()` - Status-Updates
- `match_file_to_enrollment()` - Fuzzy Name-Matching

**Geschätzte Tests:** 15-20

#### 4.1.3 Email CLI Unit Tests (5h)
**Datei erstellen:** `tests/unit/test_email_cli.py`

Tests für:
- `decode_email_header()` - Header-Dekodierung
- `extract_email_address()` - Email-Extraktion
- `extract_student_id_from_text()` - Matrikelnummer-Erkennung
- `match_student_by_email()` - Email-Matching
- `match_student_by_name()` - Fuzzy Name-Matching
- `parse_eml_file()` - EML-Parsing
- `parse_mbox_file()` - MBOX-Parsing

**Geschätzte Tests:** 20-25

### 4.2 MyPy Errors beheben (~3h)
**Dateien:** Verschiedene (49 Errors)

Hauptbereiche:
- Type Annotations in Services
- Return Types in CLI-Tools
- Optional Types für nullable Felder

### 4.3 Template URL Building Issues (~2h)
**Dateien:** `tests/integration/test_document_routes.py`

- 2 skipped Tests fixen
- URL-Building im Test-Context korrigieren

---

## Phase 5: Extended Features (~60-80h)

### 5.1 User Model & Authentication (~12h)

#### 5.1.1 Dependencies hinzufügen
```bash
uv add flask-login
uv add werkzeug  # für password hashing (falls nicht vorhanden)
```

#### 5.1.2 User Model erstellen
**Datei erstellen:** `app/models/user.py`

```python
class User(db.Model, UserMixin, TimestampMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="lecturer")  # admin, lecturer, viewer
    is_active = Column(Boolean, default=True)
    university_id = Column(Integer, ForeignKey("university.id"), nullable=True)

    # Relationships
    university = relationship("University", back_populates="users")
```

**Rollen:**
- `admin` - Vollzugriff auf alles
- `lecturer` - Eigene Kurse/Studenten verwalten
- `viewer` - Nur Lesezugriff

#### 5.1.3 Flask-Login Setup
**Datei ändern:** `app/__init__.py`

```python
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Bitte melden Sie sich an."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

#### 5.1.4 Auth Routes erstellen
**Datei erstellen:** `app/routes/auth.py`

Routes:
- `GET/POST /login` - Login-Formular
- `GET /logout` - Logout
- `GET/POST /register` - Registrierung (optional, Admin-only)
- `GET/POST /profile` - Profil bearbeiten
- `GET/POST /change-password` - Passwort ändern

#### 5.1.5 Auth Templates erstellen
**Dateien erstellen:**
- `app/templates/auth/login.html`
- `app/templates/auth/register.html`
- `app/templates/auth/profile.html`

#### 5.1.6 Migration erstellen
```bash
alembic revision --autogenerate -m "Add user model"
alembic upgrade head
```

#### 5.1.7 UserService erstellen
**Datei erstellen:** `app/services/user_service.py`

Methoden:
- `create_user()`, `authenticate()`, `change_password()`
- `list_users()`, `get_user()`, `update_user()`, `delete_user()`

#### 5.1.8 Tests
**Dateien erstellen:**
- `tests/unit/test_user_service.py`
- `tests/integration/test_auth_routes.py`

---

### 5.2 Authorization & RBAC (~8h)

#### 5.2.1 Decorators erstellen
**Datei erstellen:** `app/utils/auth.py`

```python
from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required("admin")(f)

def lecturer_required(f):
    return role_required("admin", "lecturer")(f)
```

#### 5.2.2 Routes mit @login_required schützen
**Dateien ändern:** Alle Route-Dateien in `app/routes/`

```python
from flask_login import login_required
from app.utils.auth import lecturer_required

@bp.route("/")
@login_required
def list():
    ...

@bp.route("/delete/<int:id>", methods=["POST"])
@lecturer_required
def delete(id):
    ...
```

#### 5.2.3 Data Scoping für Multi-User
**Dateien ändern:** Services

```python
def list_courses(self, user=None, **filters):
    query = self.query(Course)
    if user and user.role != "admin":
        query = query.filter(Course.university_id == user.university_id)
    return query.all()
```

---

### 5.3 Audit Trail (~10h)

#### 5.3.1 AuditLog Model
**Datei erstellen:** `app/models/audit_log.py`

```python
class AuditLog(db.Model):
    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
```

#### 5.3.2 AuditService erstellen
**Datei erstellen:** `app/services/audit_service.py`

```python
class AuditService(BaseService):
    def log_action(self, table_name, record_id, action, user_id, old_values, new_values, ip):
        ...

    def get_record_history(self, table_name, record_id):
        ...

    def get_user_activity(self, user_id, limit=100):
        ...
```

#### 5.3.3 SQLAlchemy Event Listeners
**Datei ändern:** `app/models/__init__.py`

```python
from sqlalchemy import event

@event.listens_for(db.session, "before_flush")
def audit_changes(session, flush_context, instances):
    # Log INSERT, UPDATE, DELETE
    ...
```

#### 5.3.4 Audit Route & Templates
**Datei erstellen:** `app/routes/audit.py`
**Templates:** `app/templates/audit/list.html`, `history.html`

#### 5.3.5 Extended Timestamps auf Models
**Dateien ändern:** Alle Models

```python
created_by = Column(Integer, ForeignKey("user.id"), nullable=True)
updated_by = Column(Integer, ForeignKey("user.id"), nullable=True)
```

---

### 5.4 REST API (~15h)

#### 5.4.1 Dependencies hinzufügen
```bash
uv add marshmallow
uv add marshmallow-sqlalchemy
uv add flask-cors  # für Cross-Origin Requests
```

#### 5.4.2 API Blueprint Struktur
**Verzeichnis erstellen:** `app/routes/api/v1/`

```
app/routes/api/
├── __init__.py
└── v1/
    ├── __init__.py
    ├── students.py
    ├── universities.py
    ├── courses.py
    ├── enrollments.py
    ├── exams.py
    ├── grades.py
    └── documents.py
```

#### 5.4.3 Schemas erstellen (Marshmallow)
**Verzeichnis erstellen:** `app/schemas/`

```python
# app/schemas/student.py
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class StudentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        include_relationships = True
        load_instance = True
```

#### 5.4.4 API Response Helpers
**Datei erstellen:** `app/utils/api.py`

```python
def api_response(data=None, message=None, status=200):
    return jsonify({
        "success": status < 400,
        "data": data,
        "message": message
    }), status

def api_error(message, status=400, errors=None):
    return jsonify({
        "success": False,
        "message": message,
        "errors": errors
    }), status
```

#### 5.4.5 API Endpoints implementieren
Für jede Resource:
- `GET /api/v1/students` - Liste (mit Pagination)
- `GET /api/v1/students/<id>` - Detail
- `POST /api/v1/students` - Erstellen
- `PUT /api/v1/students/<id>` - Update
- `DELETE /api/v1/students/<id>` - Löschen

#### 5.4.6 API Authentication
Session-Cookie für Web oder API-Key für externe Zugriffe:

```python
@bp.before_request
def api_auth():
    if not current_user.is_authenticated:
        api_key = request.headers.get("X-API-Key")
        if not api_key or not validate_api_key(api_key):
            return api_error("Unauthorized", 401)
```

#### 5.4.7 API Tests
**Datei erstellen:** `tests/integration/test_api_v1.py`

---

### 5.5 Extended Exports (~10h)

#### 5.5.1 Dependencies hinzufügen
```bash
uv add reportlab  # PDF Generation
uv add xlsxwriter  # Alternative zu openpyxl für bessere Performance
```

#### 5.5.2 ExportService erstellen
**Datei erstellen:** `app/services/export_service.py`

```python
class ExportService:
    def export_students_csv(self, filters) -> str: ...
    def export_students_excel(self, filters) -> bytes: ...
    def export_grades_csv(self, course_id) -> str: ...
    def export_grades_excel(self, course_id) -> bytes: ...
    def export_grades_pdf(self, course_id) -> bytes: ...
    def generate_grade_report_pdf(self, exam_id) -> bytes: ...
```

#### 5.5.3 PDF Report Templates
**Verzeichnis erstellen:** `app/templates/reports/`

- `grade_report.html` - Für Notenübersicht
- `student_list.html` - Für Studierendenliste
- `exam_results.html` - Für Prüfungsergebnisse

#### 5.5.4 Export Routes erweitern
**Dateien ändern:** `app/routes/student.py`, `grade.py`, `exam.py`

Neue Endpoints:
- `GET /students/export?format=csv|xlsx|pdf`
- `GET /grades/export?course_id=X&format=csv|xlsx|pdf`
- `GET /exams/<id>/results/export?format=csv|xlsx|pdf`

#### 5.5.5 Export CLI
**Datei erstellen:** `cli/export_cli.py`

```bash
python cli/export_cli.py students --format xlsx --output students.xlsx
python cli/export_cli.py grades --course-id 1 --format pdf --output grades.pdf
```

---

### 5.6 Email Notifications (~10h)

#### 5.6.1 Dependencies hinzufügen
```bash
uv add flask-mail
```

#### 5.6.2 Mail Configuration
**Datei ändern:** `config.py`

```python
# Email Configuration
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.example.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@example.com")
```

#### 5.6.3 Flask-Mail Setup
**Datei ändern:** `app/__init__.py`

```python
from flask_mail import Mail

mail = Mail()

def create_app(config_name):
    ...
    mail.init_app(app)
```

#### 5.6.4 NotificationService erstellen
**Datei erstellen:** `app/services/notification_service.py`

```python
class NotificationService:
    def send_grade_notification(self, student, grade): ...
    def send_enrollment_confirmation(self, student, course): ...
    def send_exam_reminder(self, course, exam): ...
    def send_bulk_notification(self, recipients, subject, template, **context): ...
```

#### 5.6.5 Email Templates
**Verzeichnis erstellen:** `app/templates/emails/`

- `grade_notification.html` / `.txt`
- `enrollment_confirmation.html` / `.txt`
- `exam_reminder.html` / `.txt`
- `base_email.html` - Basis-Template

#### 5.6.6 Notification Settings
**Model erweitern:** `app/models/user.py`

```python
# Notification preferences
notify_on_grade = Column(Boolean, default=True)
notify_on_enrollment = Column(Boolean, default=True)
```

#### 5.6.7 Async Email (Optional)
Für bessere Performance:
```bash
uv add celery redis
```

---

## Migrations-Übersicht

| Nr | Migration | Beschreibung |
|----|-----------|--------------|
| 1 | `add_user_model` | User mit Rollen, Passwort-Hash |
| 2 | `add_audit_log` | AuditLog Tabelle |
| 3 | `add_user_relations` | created_by/updated_by auf allen Models |
| 4 | `add_api_keys` | Optional: API Key Tabelle |
| 5 | `add_notification_prefs` | User Notification Settings |

---

## Neue Dependencies

```toml
# pyproject.toml - hinzufügen
dependencies = [
    # ... existing ...
    # Authentication
    "flask-login>=0.6.3",
    # API
    "marshmallow>=3.20.0",
    "marshmallow-sqlalchemy>=0.29.0",
    "flask-cors>=4.0.0",
    # Export
    "reportlab>=4.0.0",
    # Email
    "flask-mail>=0.9.1",
]
```

---

## Implementierungsreihenfolge

```
Week 1: Phase 4 - Code Quality
├── Day 1-2: GradeService Tests
├── Day 2-3: DocumentService Tests
├── Day 3-4: Email CLI Tests
└── Day 4-5: MyPy Errors, Template Issues

Week 2: Authentication & Authorization
├── Day 1-2: User Model, Flask-Login Setup
├── Day 2-3: Auth Routes & Templates
├── Day 3-4: RBAC Decorators
└── Day 4-5: Route Protection, Tests

Week 3: Audit Trail & API Foundation
├── Day 1-2: AuditLog Model & Service
├── Day 2-3: Event Listeners, Audit Routes
├── Day 3-4: API Structure, Schemas
└── Day 4-5: First API Endpoints

Week 4: API Completion & Exports
├── Day 1-2: Remaining API Endpoints
├── Day 2-3: API Tests
├── Day 3-4: Export Service (CSV, Excel, PDF)
└── Day 4-5: Export Routes & CLI

Week 5: Email Notifications & Polish
├── Day 1-2: Flask-Mail Setup
├── Day 2-3: Notification Service & Templates
├── Day 3-4: Integration Tests
└── Day 4-5: Documentation, Final Testing
```

---

## Verifikation

### Nach Phase 4:
```bash
# Test Coverage prüfen
pytest --cov=app --cov=cli --cov-report=term-missing
# Sollte >= 60% sein

# MyPy prüfen
mypy app/ cli/
# Sollte 0 Errors sein

# Alle Tests laufen
pytest -v
# Sollte 0 Failures haben
```

### Nach Phase 5:
```bash
# Server starten
python run.py

# Test Login
curl -X POST http://localhost:5009/login -d "username=admin&password=admin"

# Test API
curl -H "Cookie: session=..." http://localhost:5009/api/v1/students

# Test Export
curl -O http://localhost:5009/students/export?format=xlsx

# Test Email (mit Mailhog oder ähnlichem)
# Notification bei Grade-Erstellung prüfen
```

---

## Kritische Dateien

### Zu erstellen:
- `app/models/user.py`
- `app/models/audit_log.py`
- `app/routes/auth.py`
- `app/routes/audit.py`
- `app/routes/api/v1/*.py`
- `app/services/user_service.py`
- `app/services/audit_service.py`
- `app/services/export_service.py`
- `app/services/notification_service.py`
- `app/schemas/*.py`
- `app/utils/auth.py`
- `app/utils/api.py`
- `tests/unit/test_grade_service.py`
- `tests/unit/test_document_service.py`
- `tests/unit/test_email_cli.py`
- `tests/unit/test_user_service.py`
- `tests/integration/test_auth_routes.py`
- `tests/integration/test_api_v1.py`
- `cli/export_cli.py`

### Zu ändern:
- `app/__init__.py` - Flask-Login, Flask-Mail init
- `app/models/__init__.py` - Event Listeners
- `config.py` - Mail, CORS Settings
- `pyproject.toml` - Dependencies
- Alle `app/routes/*.py` - @login_required
- Alle `app/services/*.py` - User-Scoping
- Alle `app/models/*.py` - created_by/updated_by

---

## Risiken & Mitigationen

| Risiko | Mitigation |
|--------|------------|
| Breaking Changes durch Auth | Feature Flag für schrittweises Rollout |
| Performance bei Audit Logging | Async Logging, Batch Inserts |
| Email-Delivery Probleme | Queue-System (Celery), Retry Logic |
| API Backward Compatibility | Versionierung (/api/v1/) |
| Test-Instabilität | Fixtures isolieren, Transactions |
