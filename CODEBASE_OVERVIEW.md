# Dozentenmanager Codebase Overview

A comprehensive Flask-based student management system for university lecturers.

## Architecture

```
Routes (HTTP endpoints)
        ↓
Services (business logic)
        ↓
Models (database layer)
```

**Key Patterns:**
- Application Factory Pattern
- Blueprint Pattern (modular routes)
- Service Layer Pattern
- CLI-First Development Workflow

---

## Project Structure

```
dozentenmanager/
├── app/                          # Flask application core
│   ├── __init__.py              # App factory
│   ├── models/                   # SQLAlchemy models (11)
│   ├── routes/                   # Flask blueprints (8)
│   ├── services/                 # Business logic (8)
│   ├── forms/                    # WTForms
│   ├── templates/                # Jinja2 templates (44)
│   ├── static/                   # CSS/JS assets
│   └── utils/                    # Helpers
├── cli/                          # CLI tools (9)
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests (6 files)
│   └── integration/             # Integration tests (9 files)
├── migrations/                   # Alembic migrations
├── uploads/                      # User uploads
├── config.py                     # Configuration
├── run.py                        # Entry point
└── ref/                         # Reference docs
```

---

## Database Models (11 total)

| Model | Purpose | Key Fields |
|-------|---------|------------|
| **University** | Educational institutions | id, name, slug, location, timestamps |
| **Student** | Student records | id, first_name, last_name, student_id (8 digits), email, program, deleted_at (soft delete) |
| **Course** | University courses | id, name, slug, semester (YYYY_SoSe/WiSe), university_id (FK) |
| **Enrollment** | Student-Course relationship | id, student_id (FK), course_id (FK), status (active/completed/dropped), dates |
| **Exam** | Course assessments | id, name, course_id (FK), exam_date, max_points, weight (0-100%) |
| **ExamComponent** | Multi-part exam sections | id, exam_id (FK), name, weight, max_points, order |
| **Grade** | Student exam results | id, enrollment_id (FK), exam_id (FK), points, percentage, grade_value, is_final |
| **GradingScale** | Custom grade thresholds | id, name, university_id (FK), is_default |
| **GradeThreshold** | Grade boundaries | id, scale_id (FK), grade_value, grade_label, min_percentage |
| **Submission** | Document submissions | id, enrollment_id (FK), exam_id (FK), submission_type, status |
| **Document** | Uploaded files | id, submission_id (FK), filename, file_path, file_type, file_size |

**Features:**
- TimestampMixin on all models (created_at, updated_at)
- Soft deletes for Students
- German grading scale (1.0-5.0)
- Comprehensive validations

---

## Services Layer (8 services)

| Service | Lines | Key Methods |
|---------|-------|-------------|
| **BaseService** | 69 | commit(), rollback(), add(), delete(), query() |
| **StudentService** | 362 | add_student(), list_students(), get_student(), update_student(), delete_student() |
| **UniversityService** | 284 | add_university(), list_universities(), get_university(), update_university(), delete_university() |
| **CourseService** | 293 | add_course(), list_courses(), get_course(), update_course(), delete_course() |
| **EnrollmentService** | 298 | add_enrollment(), list_enrollments(), get_enrollment(), remove_enrollment(), update_status() |
| **ExamService** | 271 | add_exam(), list_exams(), get_exam(), update_exam(), delete_exam() |
| **GradeService** | 602 | add_grade(), update_grade(), calculate_weighted_average(), get_exam_statistics(), add_exam_component() |
| **DocumentService** | 545 | get_upload_path(), create_submission(), upload_document(), list_documents(), match_file_to_enrollment() |

---

## Web Routes (8 blueprints)

| Blueprint | URL Prefix | Lines | Key Features |
|-----------|------------|-------|--------------|
| **student.py** | `/students` | 634 | Bulk import (CSV/XLSX), export, pagination |
| **university.py** | `/universities` | 285 | Dashboard stats |
| **course.py** | `/courses` | 339 | Semester filtering |
| **enrollment.py** | `/enrollments` | 242 | Bulk operations |
| **exam.py** | `/exams` | 268 | Course-based queries |
| **grade.py** | `/grades` | 599 | Dashboard, statistics, components, API endpoints |
| **document.py** | `/documents` | 774 | File upload, email import, bulk upload |
| **backup.py** | `/backups` | 143 | Database export |

**Total: ~3,400 lines, ~70+ HTTP endpoints**

---

## CLI Tools (9 modules)

| Module | Size | Commands |
|--------|------|----------|
| **student_cli.py** | 14.9 KB | add, list, export, import (CSV/XLSX), delete |
| **university_cli.py** | 5.2 KB | add, list, update, delete |
| **course_cli.py** | 7.5 KB | add, list, update, delete |
| **enrollment_cli.py** | 7.2 KB | add, list, remove, status update |
| **exam_cli.py** | 9.0 KB | add, list, update, delete |
| **grade_cli.py** | 14.4 KB | add, update, delete, list, statistics, components |
| **document_cli.py** | 9.5 KB | upload, list, delete, match files |
| **email_cli.py** | 22.7 KB | Parse emails, extract attachments, auto-match |
| **backup_cli.py** | 12.9 KB | Export/import database |

**Total: ~2,900 lines**

---

## Templates (44 total)

**Base:**
- `base.html` - Master layout (Bulma CSS + Font Awesome)
- `_pagination.html` - Shared pagination

**By Feature:**
- Student: 5 templates
- University: 4 templates
- Course: 4 templates
- Enrollment: 1 template
- Exam: 4 templates
- Grade: 10 templates
- Document: 8 templates
- Backup: 1 template
- Errors: 2 templates (404, 500)

**Frontend Stack:**
- Bulma CSS 1.0.2
- Font Awesome 6.4.0
- Dark mode support (theme-switcher.js)

---

## Testing

| Category | Files | Size |
|----------|-------|------|
| **Integration Tests** | 9 | ~136 KB |
| **Unit Tests** | 6 | ~112 KB |

**Coverage:**
- 251 tests total
- 100% pass rate
- Minimum 40% coverage requirement

---

## Configuration

**Three Environments:**
- `DevelopmentConfig` - Debug=True, SQLite
- `TestingConfig` - In-memory SQLite, CSRF disabled
- `ProductionConfig` - Debug=False, requires SECRET_KEY

**Key Settings:**
- Database: SQLite (configurable)
- Max file size: 16 MB
- Allowed extensions: pdf, doc, docx, txt, odt, rtf

---

## Dependencies

**Core:**
- Flask 3.1.2+
- SQLAlchemy 2.0.44+
- Alembic 1.17.1+
- Flask-WTF 1.2.2+

**Development:**
- pytest 8.4.2+
- mypy 1.18.2+
- ruff 0.14.3+
- Playwright 1.57.0+

---

## File Upload Structure

```
uploads/
└── {university_slug}/
    └── {semester}/
        └── {course_slug}/
            └── {LastnameFirstname}/
                └── [files]

Example:
uploads/th-koeln/2023_SoSe/einfuehrung-statistik/MuellerMike/
```

---

## Security Features

- Email validation (regex)
- Student ID format validation (8 digits)
- Semester format validation (YYYY_SoSe/WiSe)
- Filename sanitization
- File extension whitelist
- File size limits
- CSRF protection (Flask-WTF)
- Unique constraints prevent duplicates

---

## Code Statistics

| Metric | Value |
|--------|-------|
| Total Python Code | ~7,500+ lines |
| Models | 11 |
| Services | 8 |
| Route Blueprints | 8 |
| CLI Tools | 9 |
| Templates | 44 |
| Tests | 251 |
| HTTP Endpoints | ~70+ |

---

## Data Flow Examples

### Adding a Student (CLI)
```
student_cli.py add → StudentService.add_student() → Student model → Database
```

### Adding a Student (Web)
```
GET /students/new → StudentForm → POST /students/ → StudentService → Redirect
```

### Grading Workflow
1. Create Exam (max_points, weight)
2. Optionally add ExamComponents
3. Submit Grade via web or CLI
4. GradeService auto-calculates percentage and German grade
5. Mark as final when ready

---

*Generated: 2026-01-23*
