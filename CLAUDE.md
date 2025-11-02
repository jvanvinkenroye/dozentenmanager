# CLAUDE.md - Dozentenmanager

Project-specific instructions for Claude Code when working with this repository.

## Project Overview

**Dozentenmanager** is a Flask-based student management system for university lecturers to manage students, courses, exams, and grading across multiple institutions.

**Current Status:** Initial planning phase. No code has been written yet.

**Primary Goal:** Build a comprehensive student management system with document processing, grading workflows, and complete audit trails.

## Technology Stack

### Core Technologies
- **Language:** Python 3.11+
- **Web Framework:** Flask
- **Database:** SQLite (with SQLAlchemy ORM)
- **Package Manager:** UV (fast Python package manager)
- **CSS Framework:** Bulma CSS

### Development Tools
- **Linting & Formatting:** Ruff
- **Type Checking:** mypy
- **Testing:** pytest
- **Migrations:** Alembic
- **Version Control:** Git

## Project Structure

```
dozentenmanager/
├── app/                    # Flask application
│   ├── models/            # Database models (SQLAlchemy)
│   ├── routes/            # Flask blueprints for web routes
│   ├── services/          # Business logic layer
│   ├── utils/             # Utilities and helpers
│   ├── templates/         # Jinja2 HTML templates
│   └── static/            # CSS, JavaScript, images
├── cli/                   # Command-line interface tools
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
├── migrations/           # Alembic database migrations
├── uploads/              # User-uploaded files
├── ref/                  # Reference documentation
├── config.py             # Configuration management
├── pyproject.toml        # Project dependencies (UV)
├── .env                  # Environment variables (not in git)
└── run.py                # Application entry point
```

## File Organization for Uploads

Files are automatically organized in this structure:
```
uploads/{university_slug}/{semester}/{course_slug}/{LastnameFirstname}/
Example: uploads/th-koeln/2023_SoSe/einfuehrung-statistik/MuellerMike/
```

## Reference Documentation

Comprehensive reference documentation is available in the `/ref` directory:

- **[Project Overview](./ref/project-overview.md)** - Purpose, functionality, target users
- **[Architecture](./ref/architecture.md)** - Technical design, system architecture, security
- **[Data Model](./ref/data-model.md)** - Database schema, relationships, SQLAlchemy models
- **[Development Workflow](./ref/development-workflow.md)** - Setup, testing, deployment procedures
- **[Features](./ref/features.md)** - Complete feature breakdown with implementation roadmap

## Development Workflow

### CRITICAL: CLI-First Development

**Always follow this sequence:**

1. **Build CLI tool first** in `cli/` directory
2. **Add comprehensive tests** (unit tests)
3. **Run linting and type checking**
4. **Commit the CLI implementation**
5. **Then create Flask route** that uses the CLI logic
6. **Add integration tests**
7. **Commit the Flask integration**

This workflow is a project requirement. Do NOT skip the CLI step.

### Example Workflow

```bash
# 1. Implement CLI tool
# Create cli/student_cli.py with add_student(), list_students(), etc.

# 2. Test it
pytest tests/unit/test_student_cli.py

# 3. Quality checks
ruff check --fix .
mypy cli/

# 4. Commit CLI
git add cli/student_cli.py tests/unit/test_student_cli.py
git commit -m "feat: add student management CLI"

# 5. Create Flask route
# Create app/routes/students.py that calls CLI functions

# 6. Integration tests
pytest tests/integration/test_student_routes.py

# 7. Commit Flask integration
git add app/routes/students.py tests/integration/test_student_routes.py
git commit -m "feat: add student management web interface"
```

## Code Quality Standards

### Before Every Commit

```bash
# 1. Format and lint
ruff check --fix .
ruff format .

# 2. Type checking
mypy app/ cli/

# 3. Run tests
pytest

# 4. Check coverage (optional)
pytest --cov=app --cov=cli --cov-report=html
```

### Pre-commit Hooks

This project uses pre-commit hooks. Install with:
```bash
pre-commit install
```

## Python Development Guidelines

### Virtual Environment (REQUIRED)

**Always use UV for virtual environment:**
```bash
uv venv --seed
source .venv/bin/activate  # macOS/Linux
```

**Never install packages globally.** Always work within the virtual environment.

### Code Style

1. **Type Hints Required**
   ```python
   def calculate_grade(points: float, max_points: float) -> str:
       """Calculate letter grade from points."""
       pass
   ```

2. **Docstrings Required** (Google style)
   ```python
   def add_student(first_name: str, last_name: str, student_id: str,
                   email: str, program: str) -> Student:
       """
       Add a new student to the database.

       Args:
           first_name: Student's first name
           last_name: Student's last name
           student_id: Matriculation number (unique)
           email: Student email address (unique)
           program: Study program name

       Returns:
           Student: Created student object

       Raises:
           ValueError: If email format is invalid or student_id already exists
       """
   ```

3. **Descriptive Variable Names**
   ```python
   # Good
   enrolled_students = get_students_for_course(course_id)

   # Bad
   students = get_s(cid)
   ```

4. **Error Handling**
   ```python
   try:
       student = add_student(**data)
   except ValueError as e:
       logger.error(f"Invalid student data: {e}")
       flash(f"Error: {e}", "error")
       return redirect(url_for('students.list'))
   ```

5. **Logging**
   ```python
   import logging

   logger = logging.getLogger(__name__)
   logger.info(f"Student {student_id} enrolled in course {course_id}")
   logger.warning(f"Duplicate enrollment attempt: {student_id} in {course_id}")
   logger.error(f"Database error: {e}", exc_info=True)
   ```

## Database Guidelines

### Using SQLAlchemy Models

```python
from app.models import Student, Course, Enrollment
from app import db

# Create
student = Student(
    first_name="Max",
    last_name="Mustermann",
    student_id="12345678",
    email="max@example.com"
)
db.session.add(student)
db.session.commit()

# Query
students = Student.query.filter_by(program="Computer Science").all()
student = Student.query.filter_by(student_id="12345678").first()

# Update
student.email = "new@example.com"
db.session.commit()

# Delete
db.session.delete(student)
db.session.commit()
```

### Migrations with Alembic

```bash
# Create migration after model changes
alembic revision --autogenerate -m "Add audit_log table"

# Review the generated migration file!
# Then apply it:
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Testing Guidelines

### Test Structure

- **Unit Tests** (`tests/unit/`): Test individual functions in isolation
- **Integration Tests** (`tests/integration/`): Test Flask routes with database
- **Fixtures** (`tests/fixtures/`): Sample data for tests

### Writing Tests

```python
import pytest
from cli.student_cli import add_student, validate_email

def test_validate_email():
    """Test email validation function."""
    assert validate_email("max@example.com") == True
    assert validate_email("invalid") == False
    assert validate_email("") == False

def test_add_student(test_db):
    """Test adding a new student."""
    student = add_student(
        first_name="Max",
        last_name="Mustermann",
        student_id="12345678",
        email="max@example.com",
        program="Computer Science"
    )
    assert student.id is not None
    assert student.email == "max@example.com"

    # Test duplicate prevention
    with pytest.raises(ValueError, match="already exists"):
        add_student(
            first_name="Another",
            last_name="Student",
            student_id="12345678",  # Duplicate
            email="other@example.com",
            program="Math"
        )
```

## Security Considerations

### Input Validation

Always validate user input before processing:

```python
import re

def validate_student_id(student_id: str) -> bool:
    """Validate student ID format (8 digits)."""
    return bool(re.match(r'^\d{8}$', student_id))

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path components
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename
```

### File Upload Security

```python
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file) -> bool:
    """Check if file size is within limit."""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= MAX_FILE_SIZE
```

## Git Workflow

### Commit Message Format

Use conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `chore:` - Maintenance tasks

```bash
git commit -m "feat: add student import from CSV"
git commit -m "fix: handle edge case in grade calculation"
git commit -m "test: add tests for email parser"
```

### Git Initialization

If not already a git repository:
```bash
git init
git add .
git commit -m "chore: initial project setup"
```

## Environment Variables

Create `.env` file (do NOT commit to git):

```bash
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///dozentenmanager.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

## Running the Application

### Development Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Set environment
export FLASK_ENV=development

# Run Flask
flask run

# Or with auto-reload
flask run --reload
```

### CLI Tools

```bash
# Run CLI tools directly
python cli/student_cli.py add --first-name Max --last-name Mustermann \
  --student-id 12345678 --email max@example.com --program "Computer Science"
```

## Common Tasks

### Add a New Feature

See `/ref/development-workflow.md` for detailed workflow.

Summary:
1. Create CLI tool in `cli/`
2. Write unit tests
3. Run quality checks (ruff, mypy)
4. Commit CLI
5. Create Flask route in `app/routes/`
6. Write integration tests
7. Commit Flask integration

### Add a New Model

1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Create migration: `alembic revision --autogenerate -m "Add model_name"`
4. Review migration file
5. Apply: `alembic upgrade head`
6. Write tests

### Add Dependencies

```bash
# Add runtime dependency
uv add flask-mail

# Add development dependency
uv add --dev pytest-cov
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Check if venv is active
which python  # Should point to .venv/bin/python

# Recreate venv if needed
rm -rf .venv
uv venv --seed
source .venv/bin/activate
```

### Database Issues

```bash
# Reset database (development only!)
rm dev_dozentenmanager.db
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Platform Compatibility

This project must run on **macOS and Linux**.

- Use `pathlib` for cross-platform path handling
- Use `os.path.join()` or `Path()` instead of hardcoded separators
- Test on both platforms when possible

## Key Design Patterns

### Factory Pattern
Flask app uses application factory pattern for testability.

### Repository Pattern
Business logic in `services/`, separated from data access.

### Blueprint Pattern
Routes organized by feature using Flask blueprints.

## Important Conventions

### Naming
- **Files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/Variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Database Tables:** `singular_lowercase` (e.g., `student`, not `students`)

### Imports Organization

```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party
from flask import Flask, render_template
from sqlalchemy import Column, Integer, String

# Local
from app.models import Student
from app.utils import validate_email
```

## When in Doubt

1. **Check the reference docs** in `/ref/`
2. **Follow the CLI-first workflow**
3. **Write tests before committing**
4. **Run linting and type checking**
5. **Use descriptive names and add docstrings**
6. **Log important operations**
7. **Validate all user input**

## Next Steps

Since this is a new project, the first development task should be:

1. Initialize git repository (if not done)
2. Set up virtual environment with UV
3. Create `pyproject.toml` with initial dependencies
4. Set up project structure (directories)
5. Configure Ruff, mypy, and pre-commit
6. Create `.gitignore` for Python/Flask
7. Create basic Flask app factory
8. Set up Alembic for migrations
9. Implement first feature: University Management (following CLI-first workflow)

See `/ref/features.md` for the complete feature roadmap and implementation order.
