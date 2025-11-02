# Changelog

All notable changes to the Dozentenmanager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Next features in development will be listed here

## [0.3.0] - 2025-11-02

### Added
- **Course Management System** (CLI + Web)
  - Course model with semester validation and slug generation
  - Semester format validation (YYYY_SoSe or YYYY_WiSe)
  - Automatic slug generation from course names (handles German umlauts)
  - Foreign key relationship to University
  - Unique constraint on university_id + semester + slug combination
  - Database migration with indexes on semester and university_id
  - CLI tool (`cli/course_cli.py`) with full CRUD operations:
    - Add courses with semester validation and university selection
    - List courses with search (name) and filters (university/semester)
    - Show course details
    - Update course information with auto-slug regeneration
    - Delete courses
  - Flask blueprint for course management routes
  - Responsive Bulma-based templates:
    - List view with search and dual filters (university dropdown + semester)
    - Detail view showing course and university information
    - Create/edit form with semester pattern validation and help sidebar
    - Delete confirmation page with warnings about related data
  - 28 unit tests for CLI operations
  - Navigation updated with courses link (Lehrveranstaltungen)
  - Integration with existing Flask application

### Changed
- Updated base template navigation to include courses section
- Registered course blueprint in Flask app factory

### Fixed
- SQLAlchemy DetachedInstanceError in test fixtures (return IDs instead of objects)
- IntegrityError test assertions for unique constraint violations
- Type checking for SQLAlchemy exception handling

### Technical
- Total test count: 122 tests (61 university + 33 student + 28 course)
- All tests passing with 100% success rate
- Linting clean (ruff)
- Type checking passing (mypy)
- Pre-commit hooks configured and passing

## [0.2.0] - 2025-11-02

### Added
- **Student Management System** (CLI + Web)
  - Student model with email and student_id validations
  - Email format validation using regex
  - Student ID validation (8 digits)
  - Database migration with indexes on student_id, email, and last_name
  - CLI tool (`cli/student_cli.py`) with full CRUD operations:
    - Add students with comprehensive validation
    - List students with search (name/student_id/email) and filter by program
    - Show student details
    - Update student information
    - Delete students
  - Flask blueprint for student management routes
  - Responsive Bulma-based templates:
    - List view with search and filter capabilities
    - Detail view showing student information
    - Create/edit form with client and server-side validation
    - Delete confirmation page
  - 33 unit tests for CLI operations
  - Navigation updated with students link
  - Integration with existing Flask application

### Changed
- Updated base template navigation to include students section
- Updated home page with student management link

### Technical
- Total test count: 94 tests (61 university + 33 student)
- All tests passing with 100% success rate
- Linting clean (ruff)
- Type checking passing (mypy)
- Pre-commit hooks configured and passing

## [0.1.0] - 2025-11-02

### Added
- **University Management System** (CLI + Web)
  - University model with slug-based URL identifiers
  - Automatic slug generation from university names (handles German umlauts)
  - Slug validation (lowercase letters, numbers, hyphens only)
  - Database migration with indexes on slug field
  - CLI tool (`cli/university_cli.py`) with full CRUD operations:
    - Add universities with auto-generated or custom slugs
    - List universities with search functionality
    - Show university details
    - Update university name or slug
    - Delete universities
  - Flask blueprint for university management routes
  - Responsive Bulma-based templates:
    - List view with search functionality
    - Detail view with university information
    - Create/edit form with validation
    - Delete confirmation page
  - 40 unit tests for CLI operations
  - 21 integration tests for web routes

### Changed
- Updated `.gitignore` to exclude `.claude/` directory

### Technical
- Total test count: 61 tests (40 unit + 21 integration)
- All tests passing
- Ruff linting configured and passing
- Mypy type checking configured and passing

## [0.0.1] - 2025-11-02

### Added
- **Project Setup & Infrastructure**
  - Git repository initialization
  - Virtual environment setup with UV package manager
  - Python project initialization with `pyproject.toml`
  - Core dependencies: Flask, SQLAlchemy, Alembic, python-dotenv
  - Development dependencies: pytest, ruff, mypy, pre-commit
  - Configuration system (`config.py`) with Development/Testing/Production configs
  - Environment configuration (`.env.example`)
  - Pre-commit hooks for code quality:
    - Ruff linting and formatting
    - Mypy type checking
    - Various file consistency checks
  - Project directory structure:
    - `app/` - Flask application
    - `app/models/` - Database models
    - `app/routes/` - Flask blueprints
    - `app/templates/` - Jinja2 templates
    - `app/static/` - Static files (CSS, JS, images)
    - `cli/` - CLI tools
    - `tests/unit/` - Unit tests
    - `tests/integration/` - Integration tests
    - `migrations/` - Alembic migrations
    - `logs/` - Application logs
    - `uploads/` - File uploads
  - Flask application factory pattern (`app/__init__.py`)
  - SQLAlchemy database integration with scoped sessions
  - Alembic migration system configuration
  - Base HTML template using Bulma CSS framework
  - TimestampMixin for automatic created_at/updated_at tracking
  - Comprehensive `.gitignore` for Python/Flask projects

### Technical
- Python 3.12+ required
- Flask development server configured
- SQLite database for development
- Database session management with proper teardown
- Logging configuration with rotation
- Error handlers (404, 500)
- Context processors for templates

### Documentation
- `/ref/` directory with comprehensive project documentation:
  - `project-overview.md` - Project description and goals
  - `architecture.md` - Technical architecture details
  - `data-model.md` - Complete database schema documentation
  - `development-workflow.md` - Development process and CLI-first workflow
  - `features.md` - Feature breakdown with 40+ tasks
- `CLAUDE.md` - Project guidelines and coding standards
- `todo.md` - Detailed task tracking
- `app.md` - Original German concept document

---

## Summary Statistics

### Version 0.3.0
- **Lines of Code**: ~3,000+ (CLI + web interface)
- **Models**: 3 (University, Student, Course)
- **CLI Tools**: 3
- **Web Routes**: 15 (5 per feature × 3 features)
- **Templates**: 12 (4 per feature × 3 features)
- **Tests**: 122 (101 unit + 21 integration)
- **Test Coverage**: 100% pass rate

### Commits
- Total commits: 8
- Features: 6
- Chores: 2

### Development Timeline
- Project initialized: 2025-11-02
- University Management completed: 2025-11-02
- Student Management completed: 2025-11-02
- Course Management completed: 2025-11-02
- Duration: Single day (rapid development session)

---

## Notes

- **CLI-First Workflow**: All features follow the pattern of implementing CLI first, then web interface
- **Test-Driven Development**: Comprehensive test suites ensure reliability
- **Quality Standards**: All code passes linting, type checking, and pre-commit hooks
- **German Localization**: Web interface uses German labels and text
- **Responsive Design**: Bulma CSS framework ensures mobile-friendly interface

[Unreleased]: https://github.com/yourusername/dozentenmanager/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/yourusername/dozentenmanager/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/dozentenmanager/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/dozentenmanager/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/yourusername/dozentenmanager/releases/tag/v0.0.1
