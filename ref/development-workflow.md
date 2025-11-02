# Development Workflow

## Project Setup

### Initial Setup

1. **Verify git repository status:**
   ```bash
   git status
   # If not a git repo, initialize:
   git init
   ```

2. **Create virtual environment with UV:**
   ```bash
   uv venv --seed
   source .venv/bin/activate  # On macOS/Linux
   ```

3. **Initialize project structure:**
   ```bash
   # Create pyproject.toml
   uv init
   ```

4. **Install core dependencies:**
   ```bash
   uv add flask sqlalchemy alembic python-dotenv
   uv add --dev pytest ruff mypy pre-commit
   ```

5. **Create project structure:**
   ```bash
   mkdir -p app/{models,routes,services,utils,templates,static}
   mkdir -p cli tests/{unit,integration} migrations uploads ref
   touch app/__init__.py config.py run.py
   ```

## Development Process

### Phase 1: CLI Tools First

Following the requirement to build CLI tools first, then integrate into Flask:

1. **Feature Development Sequence:**
   - Implement core functionality as CLI tool in `cli/` directory
   - Write unit tests for CLI tool
   - Add type hints and docstrings
   - Run linting and type checking
   - Commit the CLI implementation
   - Create Flask route wrapper
   - Write integration tests
   - Commit the Flask integration

2. **Example Workflow - Student Management:**
   ```bash
   # 1. Create CLI tool
   touch cli/student_cli.py
   # Implement: add_student, list_students, update_student, delete_student

   # 2. Write tests
   touch tests/unit/test_student_cli.py
   pytest tests/unit/test_student_cli.py

   # 3. Lint and type check
   ruff check cli/student_cli.py
   mypy cli/student_cli.py

   # 4. Commit
   git add cli/student_cli.py tests/unit/test_student_cli.py
   git commit -m "feat: add student management CLI tool"

   # 5. Create Flask route
   touch app/routes/students.py
   # Implement Flask routes that use the CLI logic

   # 6. Integration tests
   touch tests/integration/test_student_routes.py
   pytest tests/integration/test_student_routes.py

   # 7. Commit
   git add app/routes/students.py tests/integration/test_student_routes.py
   git commit -m "feat: add student management web interface"
   ```

### Phase 2: Code Quality Checks

Run these checks before every commit:

1. **Linting with Ruff:**
   ```bash
   # Check for issues
   ruff check .

   # Auto-fix issues
   ruff check --fix .

   # Format code
   ruff format .
   ```

2. **Type Checking with mypy:**
   ```bash
   mypy app/ cli/
   ```

3. **Run Tests:**
   ```bash
   # All tests
   pytest

   # With coverage
   pytest --cov=app --cov=cli --cov-report=html

   # Specific test file
   pytest tests/unit/test_student_cli.py -v
   ```

### Phase 3: Commit

Follow conventional commit format:

```bash
git add .
git commit -m "feat: add student import/export functionality"
git commit -m "fix: handle edge case in grade calculation"
git commit -m "docs: update API documentation"
git commit -m "test: add tests for email parser"
git commit -m "refactor: extract grading logic to service"
```

**Commit Message Format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `style:` - Code style changes (formatting, etc.)
- `chore:` - Maintenance tasks

## Pre-commit Hooks

Set up pre-commit hooks to automate quality checks:

1. **Create `.pre-commit-config.yaml`:**
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.6
       hooks:
         - id: ruff
           args: [--fix]
         - id: ruff-format

     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.7.1
       hooks:
         - id: mypy
           additional_dependencies: [types-all]

     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.5.0
       hooks:
         - id: trailing-whitespace
         - id: end-of-file-fixer
         - id: check-yaml
         - id: check-added-large-files
   ```

2. **Install hooks:**
   ```bash
   pre-commit install
   ```

3. **Run manually:**
   ```bash
   pre-commit run --all-files
   ```

## Testing Strategy

### Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_student_cli.py
│   ├── test_grading_service.py
│   └── test_validators.py
├── integration/             # Tests with database
│   ├── test_student_routes.py
│   ├── test_enrollment_flow.py
│   └── test_document_upload.py
└── fixtures/                # Test data
    ├── sample_students.json
    └── test_documents/
```

### Writing Tests

**Unit Test Example:**
```python
import pytest
from cli.student_cli import add_student, validate_student_id

def test_validate_student_id():
    """Test student ID validation."""
    assert validate_student_id("12345678") == True
    assert validate_student_id("abc") == False
    assert validate_student_id("") == False

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
```

**Integration Test Example:**
```python
import pytest
from flask import Flask

def test_student_list_route(client):
    """Test student list endpoint."""
    response = client.get('/students')
    assert response.status_code == 200
    assert b'Students' in response.data

def test_add_student_route(client):
    """Test adding student via web interface."""
    response = client.post('/students/add', data={
        'first_name': 'Max',
        'last_name': 'Mustermann',
        'student_id': '12345678',
        'email': 'max@example.com',
        'program': 'Computer Science'
    })
    assert response.status_code == 302  # Redirect after success
```

### Test Configuration

**conftest.py:**
```python
import pytest
from app import create_app
from app.models import db

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def test_db(app):
    """Create test database."""
    return db
```

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export FLASK_APP=run.py
export FLASK_ENV=development

# Run development server
flask run

# Or with auto-reload
flask run --reload

# Run on specific port
flask run --port 5001
```

### CLI Tools

```bash
# Run CLI tools directly
python cli/student_cli.py add --first-name Max --last-name Mustermann \
  --student-id 12345678 --email max@example.com

# Or create entry points in pyproject.toml
uv run student-mgmt add --first-name Max ...
```

## Database Migrations

### Using Alembic

1. **Initialize Alembic:**
   ```bash
   alembic init migrations
   ```

2. **Configure `alembic.ini`:**
   ```ini
   sqlalchemy.url = sqlite:///dozentenmanager.db
   ```

3. **Create migration:**
   ```bash
   # Auto-generate from models
   alembic revision --autogenerate -m "Create initial tables"

   # Create empty migration
   alembic revision -m "Add custom migration"
   ```

4. **Review migration file:**
   ```python
   # migrations/versions/xxx_create_initial_tables.py
   def upgrade():
       op.create_table('student', ...)

   def downgrade():
       op.drop_table('student')
   ```

5. **Apply migrations:**
   ```bash
   # Upgrade to latest
   alembic upgrade head

   # Upgrade one version
   alembic upgrade +1

   # Downgrade one version
   alembic downgrade -1

   # Show current version
   alembic current

   # Show migration history
   alembic history
   ```

## Logging Configuration

### Setup Logging

**app/utils/logger.py:**
```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Configure application logging."""
    if not app.debug:
        # File handler
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            'logs/dozentenmanager.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Dozentenmanager startup')
```

### Using Logging

```python
from flask import current_app

# In routes or services
current_app.logger.info(f"Student {student_id} enrolled in course {course_id}")
current_app.logger.warning(f"Failed login attempt from {ip_address}")
current_app.logger.error(f"Database error: {str(e)}", exc_info=True)
```

## Configuration Management

### config.py Structure

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///dev_dozentenmanager.db'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///dozentenmanager.db'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### Environment Variables

Create `.env` file (not committed to git):
```bash
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///dozentenmanager.db
```

## Documentation Standards

### Code Documentation

1. **Module docstrings:**
   ```python
   """
   Student management CLI tool.

   This module provides command-line interface for managing student records,
   including adding, updating, listing, and deleting students.
   """
   ```

2. **Function docstrings (Google style):**
   ```python
   def calculate_grade(points: float, max_points: float) -> str:
       """
       Calculate letter grade from points.

       Args:
           points: Points achieved by student
           max_points: Maximum possible points

       Returns:
           Letter grade as string (e.g., "1.0", "2.3")

       Raises:
           ValueError: If points exceed max_points

       Examples:
           >>> calculate_grade(90, 100)
           '1.3'
       """
   ```

3. **Type hints everywhere:**
   ```python
   from typing import List, Optional, Dict

   def get_students(course_id: int) -> List[Student]:
       """Get all students enrolled in a course."""
       pass

   def find_student(student_id: str) -> Optional[Student]:
       """Find student by ID, returns None if not found."""
       pass
   ```

## Feature Development Checklist

For each new feature:

- [ ] Design CLI interface and implement in `cli/`
- [ ] Add comprehensive docstrings and type hints
- [ ] Write unit tests with >80% coverage
- [ ] Run linting: `ruff check --fix .`
- [ ] Run type checking: `mypy cli/`
- [ ] Run tests: `pytest`
- [ ] Commit CLI implementation
- [ ] Design Flask route and implement in `app/routes/`
- [ ] Create HTML template in `app/templates/`
- [ ] Add integration tests
- [ ] Test manually in browser
- [ ] Run full test suite
- [ ] Commit Flask integration
- [ ] Update documentation if needed

## Deployment Workflow

### Preparing for Deployment

1. **Run full test suite:**
   ```bash
   pytest --cov=app --cov=cli
   ```

2. **Security checks:**
   ```bash
   pip-audit  # Check for vulnerable dependencies
   ```

3. **Build documentation:**
   ```bash
   # If using sphinx or similar
   cd docs && make html
   ```

4. **Create production build:**
   ```bash
   # Set production environment
   export FLASK_ENV=production

   # Run with production server (gunicorn)
   uv add gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

### Database Backup

```bash
# Backup SQLite database
cp dozentenmanager.db dozentenmanager_backup_$(date +%Y%m%d).db

# Backup with compression
sqlite3 dozentenmanager.db ".backup 'backup.db'" && \
  tar czf backup_$(date +%Y%m%d).tar.gz backup.db && \
  rm backup.db
```

## Troubleshooting

### Common Issues

1. **Virtual environment not activated:**
   ```bash
   which python  # Should point to .venv/bin/python
   source .venv/bin/activate
   ```

2. **Database migration errors:**
   ```bash
   # Reset database (development only!)
   rm dev_dozentenmanager.db
   alembic upgrade head
   ```

3. **Import errors:**
   ```bash
   # Ensure PYTHONPATH includes project root
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

4. **Port already in use:**
   ```bash
   # Find and kill process using port 5000
   lsof -ti:5000 | xargs kill -9
   ```

## Performance Monitoring

### Development Profiling

```python
# Add profiling to routes
from flask import request
import time

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        if elapsed > 1.0:  # Log slow requests
            app.logger.warning(
                f"Slow request: {request.path} took {elapsed:.2f}s"
            )
    return response
```

### Database Query Optimization

```python
# Enable SQLAlchemy query logging
app.config['SQLALCHEMY_ECHO'] = True

# Profile specific queries
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.1:  # Log slow queries
        app.logger.warning(f"Slow query ({total:.2f}s): {statement}")
```
