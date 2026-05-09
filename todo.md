# Dozentenmanager - TODO

Project task tracker for the Dozentenmanager student management system.

**Last Updated:** 2026-01-24

---

## Project Setup & Initialization

### Git & Version Control
- [x] Initialize git repository
- [x] Create initial commit with documentation
- [x] Set up GitHub/GitLab remote repository (optional)
- [x] Configure branch protection rules (optional)

### Python Environment
- [x] Verify Python 3.11+ is installed
- [x] Create virtual environment: `uv venv --seed`
- [x] Activate virtual environment
- [x] Initialize UV project: `uv init`

### Dependencies & Configuration
- [x] Add core dependencies:
  - [x] `uv add flask`
  - [x] `uv add sqlalchemy`
  - [x] `uv add alembic`
  - [x] `uv add python-dotenv`
- [x] Add development dependencies:
  - [x] `uv add --dev pytest`
  - [x] `uv add --dev ruff`
  - [x] `uv add --dev mypy`
  - [x] `uv add --dev pre-commit`
- [x] Create `.env.example` file
- [x] Create `.env` file (local, not committed)
- [x] Configure `config.py` with Development/Testing/Production configs

### Pre-commit Hooks
- [x] Create `.pre-commit-config.yaml`
- [x] Install pre-commit hooks: `pre-commit install`
- [x] Test pre-commit: `pre-commit run --all-files`

### Project Structure
- [x] Create directory structure:
  - [x] `app/` (Flask application)
  - [x] `app/models/`
  - [x] `app/routes/`
  - [x] `app/services/`
  - [x] `app/utils/`
  - [x] `app/templates/`
  - [x] `app/static/css/`
  - [x] `app/static/js/`
  - [x] `app/static/images/`
  - [x] `cli/` (CLI tools)
  - [x] `tests/unit/`
  - [x] `tests/integration/`
  - [x] `tests/fixtures/`
  - [x] `migrations/`
  - [x] `logs/`
  - [x] `uploads/` (with .gitkeep)

### Flask Application Skeleton
- [x] Create `run.py` entry point
- [x] Create `app/__init__.py` with app factory
- [x] Create base configuration in `config.py`
- [x] Test Flask app runs: `flask run`

### Database Setup
- [x] Initialize Alembic: `alembic init migrations`
- [x] Configure `alembic.ini` with database URL
- [x] Configure `migrations/env.py` to use models
- [x] Test migration: `alembic revision -m "Initial migration"`

### Template & Static Files
- [x] Download Bulma CSS or set up CDN link
- [x] Create `templates/base.html` base template
- [x] Create `static/css/custom.css` for custom styles
- [x] Test template rendering

---

## Phase 1: Core Data Management

### 1.1 University Management

#### CLI Implementation
- [x] Create `cli/university_cli.py`
- [x] Implement `add_university(name, slug)` function
- [x] Implement `list_universities()` function
- [x] Implement `get_university(id)` function
- [x] Implement `update_university(id, **kwargs)` function
- [x] Implement `delete_university(id)` function
- [x] Add argument parser with `--help`
- [x] Add input validation (required fields, unique slug)
- [x] Add logging
- [x] Add docstrings and type hints

#### Database
- [x] Create `app/models/university.py` model
- [x] Add TimestampMixin for created_at/updated_at
- [x] Create migration: `alembic revision --autogenerate -m "Add university table"`
- [x] Review and edit migration file
- [x] Apply migration: `alembic upgrade head`

#### Testing
- [x] Create `tests/unit/test_university_cli.py`
- [x] Test add_university function
- [x] Test list_universities function
- [x] Test update_university function
- [x] Test delete_university function
- [x] Test validation (unique slug, required name)
- [x] Run tests: `pytest tests/unit/test_university_cli.py`

#### Quality Checks & Commit
- [x] Run linting: `ruff check --fix .`
- [x] Run formatting: `ruff format .`
- [x] Run type checking: `mypy cli/university_cli.py`
- [x] Commit: `git commit -m "feat: add university management CLI"`

#### Web Interface
- [x] Create `app/routes/universities.py` blueprint
- [x] Implement list universities route
- [x] Implement add university route
- [x] Implement edit university route
- [x] Implement delete university route
- [x] Create `templates/universities/list.html`
- [x] Create `templates/universities/form.html`
- [x] Create `templates/universities/delete_confirm.html`

#### Integration Testing
- [x] Create `tests/integration/test_university_routes.py`
- [x] Test list route
- [x] Test add route (GET and POST)
- [x] Test edit route
- [x] Test delete route
- [x] Run integration tests: `pytest tests/integration/`

#### Final Commit
- [x] Commit: `git commit -m "feat: add university management web interface"`

---

### 1.2 Student Management

#### CLI Implementation
- [x] Create `cli/student_cli.py`
- [x] Implement `add_student()` function
- [x] Implement `list_students()` function with search/filter
- [x] Implement `get_student()` function
- [x] Implement `update_student()` function
- [x] Implement `delete_student()` function
- [x] Add email validation function
- [x] Add student ID validation function
- [x] Add argument parser with all fields
- [x] Add logging
- [x] Add comprehensive docstrings and type hints

#### Database
- [x] Create `app/models/student.py` model
- [x] Add unique constraints on student_id and email
- [x] Add indexes on student_id, email, last_name
- [x] Create migration: `alembic revision --autogenerate -m "Add student table"`
- [x] Review migration file
- [x] Apply migration: `alembic upgrade head`

#### Testing
- [x] Create `tests/unit/test_student_cli.py`
- [x] Test add_student function
- [x] Test list_students function
- [x] Test search functionality
- [x] Test update_student function
- [x] Test delete_student function
- [x] Test email validation
- [x] Test student ID validation
- [x] Test unique constraints
- [x] Run tests: `pytest tests/unit/test_student_cli.py -v`

#### Quality Checks & Commit
- [x] Run linting: `ruff check --fix .`
- [x] Run formatting: `ruff format .`
- [x] Run type checking: `mypy cli/student_cli.py`
- [x] Run all tests: `pytest`
- [x] Commit: `git commit -m "feat: add student management CLI"`

#### Web Interface
- [x] Create `app/routes/students.py` blueprint
- [x] Implement list students route with search
- [x] Implement student detail route
- [x] Implement add student route
- [x] Implement edit student route
- [x] Implement delete student route
- [x] Create `templates/students/list.html` with search form
- [x] Create `templates/students/detail.html`
- [x] Create `templates/students/form.html`
- [x] Create `templates/students/delete_confirm.html`
- [x] Add pagination to list view

#### Integration Testing
- [x] Create `tests/integration/test_student_routes.py`
- [x] Test list route
- [x] Test search functionality
- [x] Test detail route
- [x] Test add route
- [x] Test edit route
- [x] Test delete route
- [x] Test validation errors
- [x] Run integration tests

#### Final Commit
- [x] Commit: `git commit -m "feat: add student management web interface"`

---

### 1.3 Course Management

#### CLI Implementation
- [x] Create `cli/course_cli.py`
- [x] Implement `add_course()` function
- [x] Implement `list_courses()` function with filters
- [x] Implement `get_course()` function
- [x] Implement `update_course()` function
- [x] Implement `delete_course()` function
- [x] Add semester format validation
- [x] Add automatic slug generation from name
- [x] Add logging and docstrings

#### Database
- [x] Create `app/models/course.py` model
- [x] Add foreign key to university
- [x] Add unique constraint: (university_id, semester, slug)
- [x] Add indexes on university_id, semester
- [x] Create migration: `alembic revision --autogenerate -m "Add course table"`
- [x] Apply migration: `alembic upgrade head`

#### Testing
- [x] Create `tests/unit/test_course_cli.py`
- [x] Test add_course function
- [x] Test list_courses with filters
- [x] Test semester format validation
- [x] Test slug generation
- [x] Test unique constraint
- [x] Run tests: `pytest tests/unit/test_course_cli.py -v`

#### Quality Checks & Commit
- [x] Run linting and formatting
- [x] Run type checking: `mypy cli/course_cli.py`
- [x] Run all tests
- [x] Commit: `git commit -m "feat: add course management CLI"`

#### Web Interface
- [x] Create `app/routes/courses.py` blueprint
- [x] Implement list courses route (grouped by semester)
- [x] Implement course detail route
- [x] Implement add course route
- [x] Implement edit course route
- [x] Implement delete course route
- [x] Create templates for courses
- [x] Add university selection dropdown

#### Integration Testing
- [x] Create `tests/integration/test_course_routes.py`
- [x] Test all routes
- [x] Test filtering and grouping
- [x] Run integration tests

#### Final Commit
- [x] Commit: `git commit -m "feat: add course management web interface"`

---

### 1.4 Student Enrollment

#### CLI Implementation
- [x] Create `cli/enrollment_cli.py`
- [x] Implement `enroll_student()` function
- [x] Implement `list_enrollments()` function
- [x] Implement `unenroll_student()` function
- [x] Implement `update_enrollment_status()` function
- [x] Add duplicate enrollment prevention
- [x] Add validation (student exists, course exists)
- [x] Add logging and docstrings

#### Database
- [x] Create `app/models/enrollment.py` model
- [x] Add foreign keys to student and course
- [x] Add unique constraint: (student_id, course_id)
- [x] Add indexes
- [x] Add status enum/choices
- [x] Create migration: `alembic revision --autogenerate -m "Add enrollment table"`
- [x] Apply migration: `alembic upgrade head`

#### Testing
- [x] Create `tests/unit/test_enrollment_cli.py`
- [x] Test enroll_student function
- [x] Test duplicate prevention
- [x] Test unenroll_student function
- [x] Test status transitions
- [x] Run tests

#### Quality Checks & Commit
- [x] Linting, formatting, type checking
- [x] Run all tests
- [x] Commit: `git commit -m "feat: add enrollment management CLI"`

#### Web Interface
- [x] Create `app/routes/enrollments.py` blueprint
- [x] Add enrollment form to student detail page
- [x] Add enrollment form to course detail page
- [x] Implement bulk enrollment (CSV upload)
- [x] Create enrollment management templates

#### Integration Testing
- [x] Create `tests/integration/test_enrollment_routes.py`
- [x] Test enrollment workflows
- [x] Test bulk enrollment
- [x] Run integration tests

#### Final Commit
- [x] Commit: `git commit -m "feat: add enrollment web interface"`

---

## Phase 2: Examination System

### 2.1 Exam Creation

#### CLI Implementation
- [x] Create `cli/exam_cli.py`
- [x] Implement `add_exam()` function
- [x] Implement `list_exams()` function
- [x] Implement `get_exam()` function
- [x] Implement `update_exam()` function
- [x] Implement `delete_exam()` function
- [x] Add validation (weight 0-1, positive points, due date)
- [x] Add logging and docstrings

#### Database
- [x] Create `app/models/exam.py` model
- [x] Add foreign key to course
- [x] Add indexes
- [x] Create migration
- [x] Apply migration

#### Testing & Commit
- [x] Create `tests/unit/test_exam_cli.py`
- [x] Test all functions
- [x] Test validations
- [x] Linting and type checking
- [x] Commit CLI

#### Web Interface & Integration Tests
- [x] Create `app/routes/exams.py` blueprint
- [x] Create exam management templates
- [x] Add date picker for due date
- [x] Create integration tests
- [x] Commit web interface

---

### 2.2 Multi-Part Exams (Components)

#### CLI Implementation
- [x] Create `cli/exam_component_cli.py` (Implemented in `grade_cli.py`)
- [x] Implement component CRUD functions
- [x] Add weight validation (sum to 1.0)
- [x] Add order management

#### Database
- [x] Create `app/models/exam_component.py` model
- [x] Create migration
- [x] Apply migration

#### Testing & Commit
- [x] Create unit tests
- [x] Test weight sum validation
- [x] Test order management
- [x] Commit CLI

#### Web Interface
- [x] Add component management to exam detail page
- [x] Add inline editing
- [x] Add reorder functionality (drag-drop or buttons)
- [x] Create integration tests
- [x] Commit web interface

---

### 2.3 Submission Tracking

#### CLI Implementation
- [x] Create `cli/submission_cli.py` (Implemented in `document_cli.py`)
- [x] Implement `create_submission()` function
- [x] Implement `list_submissions()` function
- [x] Implement `update_submission()` function
- [x] Add points validation (≤ max_points)
- [x] Add enrollment validation

#### Database
- [x] Create `app/models/submission.py` model
- [x] Add foreign keys to student, exam, component
- [x] Add unique constraint
- [x] Create migration
- [x] Apply migration

#### Testing & Commit
- [x] Create unit tests
- [x] Test validations
- [x] Commit CLI

#### Web Interface
- [x] Create submission overview for exam
- [x] Add submission table with all students
- [x] Add bulk update functionality
- [x] Create integration tests
- [x] Commit web interface

---

### 2.4 Grading System

#### CLI Implementation
- [x] Create `cli/grading_cli.py` (Implemented as `grade_cli.py`)
- [x] Implement `calculate_grade()` function
- [x] Implement `batch_calculate_grades()` function
- [x] Implement grade scale configuration
- [x] Add grade export to CSV (Partially implemented in `stats` command)

#### Business Logic
- [x] Create `app/services/grading_service.py` (Implemented as `grade_service.py`)
- [x] Implement grade calculation algorithms
- [x] Support German grading scale (1.0-5.0)
- [x] Support weighted component grades
- [x] Add configurable grade scales

#### Testing & Commit
- [x] Create unit tests for grade calculation
- [x] Test different grading scales
- [x] Test weighted grades
- [x] Commit grading system

#### Web Interface
- [x] Create grade entry interface (table view)
- [x] Add automatic calculation on points entry
- [x] Add manual override option
- [x] Add grade distribution chart (Chart.js)
- [x] Add export to CSV/Excel
- [x] Create integration tests
- [x] Commit web interface

---

### 2.5 Grade Monitoring

#### CLI Implementation
- [x] Create grade status reporting functions
- [ ] Implement missing grade detection

#### Web Interface
- [x] Create grading dashboard
- [x] Show ungraded submissions
- [ ] Show grading progress per course
- [ ] Add alerts for overdue grading
- [x] Commit

---

## Phase 3: Document Management

### 3.1 File Storage System

#### CLI Implementation
- [x] Create `cli/file_cli.py` (Implemented as `document_cli.py`)
- [x] Implement `upload_file()` function
- [x] Implement `list_files()` function
- [x] Implement directory organization function

#### Utilities
- [x] Create `app/utils/file_manager.py` (Implemented in `document_service.py`)
- [x] Implement `sanitize_filename()` function
- [x] Implement `allowed_file()` function
- [x] Implement `validate_file_size()` function
- [x] Implement automatic directory creation
- [x] Implement unique filename generation

#### Database
- [x] Create `app/models/document.py` model
- [x] Add file metadata fields
- [x] Create migration
- [x] Apply migration

#### Testing & Commit
- [x] Create unit tests
- [x] Test filename sanitization
- [x] Test file validation
- [x] Test directory structure
- [x] Commit CLI

#### Web Interface
- [x] Create file upload form (drag-and-drop)
- [x] Add file browser
- [x] Add download functionality
- [x] Add delete functionality
- [x] Create integration tests
- [x] Commit web interface

---

### 3.2 Email Parser

#### CLI Implementation
- [x] Create `cli/email_parser_cli.py` (Implemented as `email_cli.py`)
- [x] Implement `.mbox` file parsing
- [x] Implement `.eml` file parsing
- [ ] Implement IMAP connection (optional)
- [x] Implement attachment extraction

#### Business Logic
- [x] Create `app/services/email_parser.py` (Integrated into CLI/Service)
- [x] Implement email header parsing
- [x] Implement student matching by email
- [x] Implement student matching by student ID in subject/body
- [x] Implement student matching by name
- [x] Add unmatched email flagging

#### Dependencies
- [ ] Add `imapclient` if needed: `uv add imapclient`

#### Testing & Commit
- [x] Create test fixtures (sample emails)
- [ ] Create unit tests
- [x] Test parsing various email formats
- [x] Test student matching algorithms
- [x] Commit CLI

#### Web Interface
- [x] Create email import page
- [x] Add email list view
- [x] Add attachment assignment interface
- [x] Create integration tests
- [x] Commit web interface

---

### 3.3 Document Parser (PDF/Word)

#### CLI Implementation
- [ ] Create `cli/document_parser_cli.py`
- [ ] Implement PDF text extraction
- [ ] Implement Word text extraction
- [ ] Implement batch parsing

#### Dependencies
- [ ] Add PDF library: `uv add pypdf` or `uv add pdfplumber`
- [ ] Add Word library: `uv add python-docx`

#### Business Logic
- [ ] Create `app/services/document_parser.py`
- [ ] Implement PDF text extraction
- [ ] Implement Word text extraction
- [ ] Implement student ID detection in text
- [ ] Implement name detection in text
- [ ] Store parsed content

#### Testing & Commit
- [ ] Create test fixtures (sample PDFs and Word docs)
- [ ] Create unit tests
- [ ] Test text extraction
- [ ] Test student detection
- [ ] Commit CLI

#### Web Interface
- [ ] Add document viewer with extracted text
- [ ] Add manual text correction
- [ ] Add parsed content display
- [ ] Create integration tests
- [ ] Commit web interface

---

### 3.4 Manual Document Assignment

#### CLI Implementation
- [x] Create assignment functions in `cli/document_cli.py`
- [x] Implement `assign_document()` function (via upload/update-status)
- [x] Implement `list_unassigned_documents()` function

#### Web Interface
- [ ] Create unassigned documents dashboard
- [x] Add search and assign interface
- [x] Add bulk assignment
- [x] Add document preview
- [x] Commit

---

## Phase 4: Import/Export

### 4.1 Student Import

#### CLI Implementation
- [ ] Create `cli/import_export.py`
- [ ] Implement CSV import
- [ ] Implement Excel import
- [ ] Implement JSON import
- [ ] Add column mapping support
- [ ] Add validation and error reporting
- [ ] Add batch insert with transactions

#### Dependencies
- [ ] Add Excel support: `uv add openpyxl`

#### Testing & Commit
- [ ] Create test fixtures (sample CSV, Excel, JSON)
- [ ] Create unit tests
- [ ] Test validation
- [ ] Test error handling
- [ ] Commit CLI

#### Web Interface
- [ ] Create import page
- [ ] Add file upload
- [ ] Add column mapping interface
- [ ] Add preview before import
- [ ] Show import summary
- [ ] Commit web interface

---

### 4.2 Student Export

#### CLI Implementation
- [ ] Implement CSV export
- [ ] Implement Excel export
- [ ] Implement JSON export
- [ ] Add filter support

#### Testing & Commit
- [ ] Create unit tests
- [ ] Test export formats
- [ ] Commit CLI

#### Web Interface
- [ ] Add export button to student list
- [ ] Add format selection
- [ ] Add filter options
- [ ] Commit web interface

---

### 4.3 Grade Export

#### CLI Implementation
- [ ] Implement grade export to CSV
- [ ] Implement grade export to Excel
- [ ] Add statistics calculation

#### Testing & Commit
- [ ] Create unit tests
- [ ] Commit CLI

#### Web Interface
- [ ] Add export button to grade views
- [ ] Add custom column selection
- [ ] Commit web interface

---

## Phase 5: Audit & Logging

### 5.1 Audit Log System

#### Database
- [ ] Create `app/models/audit_log.py` model
- [ ] Create migration
- [ ] Apply migration

#### Implementation
- [ ] Create audit decorator/mixin
- [ ] Implement SQLAlchemy event listeners
- [ ] Capture INSERT, UPDATE, DELETE operations
- [ ] Store old and new values (JSON)
- [ ] Capture IP address

#### CLI Implementation
- [ ] Create `cli/audit_cli.py`
- [ ] Implement log query functions
- [ ] Implement log export

#### Testing & Commit
- [ ] Create unit tests
- [ ] Test automatic logging
- [ ] Test query functions
- [ ] Commit audit system

#### Web Interface
- [ ] Create audit log viewer
- [ ] Add filters (table, date range, action)
- [ ] Add timeline view for records
- [ ] Add export functionality
- [ ] Commit web interface

---

### 5.2 Grade Change Tracking

#### Implementation
- [ ] Use audit log for grade changes
- [ ] Create helper functions for grade history

#### Web Interface
- [ ] Add grade change history to submission detail
- [ ] Create recent changes dashboard
- [ ] Commit

---

## Phase 6: Web Interface Polish

### 6.1 UI Components (Bulma CSS)

#### Base Templates
- [x] Enhance `templates/base.html`
- [x] Add navigation menu
- [x] Add breadcrumb navigation
- [x] Style flash messages
- [x] Add footer

#### Components
- [x] Create `templates/components/nav.html` (Implemented in base.html)
- [ ] Create `templates/components/breadcrumb.html`
- [x] Create `templates/components/pagination.html`
- [x] Create `templates/components/table.html` (Implemented per view)
- [x] Create `templates/components/form_field.html` (Implemented per view)
- [ ] Create `templates/components/modal.html`
- [ ] Add loading indicators

#### Styling
- [x] Create `static/css/custom.css`
- [x] Ensure responsive design (mobile-friendly)
- [x] Add custom Bulma variables
- [x] Test on different screen sizes

---

### 6.2 Dashboard

#### Implementation
- [ ] Create `app/routes/dashboard.py` blueprint (Using home.html)
- [x] Implement homepage dashboard
- [x] Add statistics (students, courses, exams)
- [x] Add recent activity feed
- [x] Add quick actions
- [ ] Add alerts (missing grades, etc.)

#### Visualizations
- [ ] Add Chart.js: `uv add chart.js` or use CDN
- [ ] Create grade distribution chart
- [ ] Create enrollment trends chart

#### Template
- [x] Create `templates/dashboard/index.html` (home.html)
- [x] Commit dashboard

---

### 6.3 Search & Filtering

#### Implementation
- [x] Implement global search (Per module)
- [x] Add advanced filters to all list pages
- [ ] Add filter presets
- [ ] Add export filtered results

#### Testing
- [x] Test search functionality
- [x] Test filters
- [x] Commit

---

## Documentation & Deployment

### Documentation
- [x] Update README.md with installation instructions
- [ ] Add usage examples to README
- [ ] Document API endpoints (if created)
- [ ] Create user guide (optional)

### Testing & Quality
- [x] Run full test suite: `pytest`
- [x] Check test coverage: `pytest --cov=app --cov=cli`
- [ ] Ensure >80% code coverage (Current: ~49%)
- [ ] Fix any failing tests

### Production Preparation
- [ ] Create production configuration
- [ ] Add gunicorn: `uv add gunicorn`
- [ ] Test with gunicorn: `gunicorn -w 4 run:app`
- [ ] Create database backup strategy
- [ ] Set up logging for production
- [ ] Security audit (input validation, SQL injection, XSS)

### Deployment
- [ ] Choose deployment platform (Heroku, DigitalOcean, AWS, etc.)
- [ ] Configure environment variables
- [ ] Deploy application
- [ ] Test deployed application
- [ ] Set up monitoring (optional)

---

## Future Enhancements

### Authentication & Authorization
- [ ] User registration and login
- [ ] Role-based access control
- [ ] Permission system for courses
- [ ] Password reset

### Notifications
- [ ] Email notifications
- [ ] In-app notifications
- [ ] Configurable preferences

### Advanced Features
- [ ] RESTful API
- [ ] API documentation (OpenAPI/Swagger)
- [ ] LMS integration (Moodle, Canvas)
- [ ] Cloud storage integration
- [ ] Plagiarism detection

---

## Notes

- **Always follow CLI-first workflow**: CLI → Tests → Commit → Web Interface → Tests → Commit
- **Run quality checks before every commit**: Ruff, mypy, pytest
- **Keep tests updated** as features are implemented
- **Use conventional commits** for clear history
- **Update this TODO regularly** to track progress

**Reference Documentation:**
- See `/ref/features.md` for detailed feature specifications
- See `/ref/development-workflow.md` for development process
- See `CLAUDE.md` for coding standards and guidelines