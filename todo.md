# Dozentenmanager - TODO

Project task tracker for the Dozentenmanager student management system.

**Last Updated:** 2025-11-02

---

## Project Setup & Initialization

### Git & Version Control
- [ ] Initialize git repository
- [ ] Create initial commit with documentation
- [ ] Set up GitHub/GitLab remote repository (optional)
- [ ] Configure branch protection rules (optional)

### Python Environment
- [ ] Verify Python 3.11+ is installed
- [ ] Create virtual environment: `uv venv --seed`
- [ ] Activate virtual environment
- [ ] Initialize UV project: `uv init`

### Dependencies & Configuration
- [ ] Add core dependencies:
  - [ ] `uv add flask`
  - [ ] `uv add sqlalchemy`
  - [ ] `uv add alembic`
  - [ ] `uv add python-dotenv`
- [ ] Add development dependencies:
  - [ ] `uv add --dev pytest`
  - [ ] `uv add --dev ruff`
  - [ ] `uv add --dev mypy`
  - [ ] `uv add --dev pre-commit`
- [ ] Create `.env.example` file
- [ ] Create `.env` file (local, not committed)
- [ ] Configure `config.py` with Development/Testing/Production configs

### Pre-commit Hooks
- [ ] Create `.pre-commit-config.yaml`
- [ ] Install pre-commit hooks: `pre-commit install`
- [ ] Test pre-commit: `pre-commit run --all-files`

### Project Structure
- [ ] Create directory structure:
  - [ ] `app/` (Flask application)
  - [ ] `app/models/`
  - [ ] `app/routes/`
  - [ ] `app/services/`
  - [ ] `app/utils/`
  - [ ] `app/templates/`
  - [ ] `app/static/css/`
  - [ ] `app/static/js/`
  - [ ] `app/static/images/`
  - [ ] `cli/` (CLI tools)
  - [ ] `tests/unit/`
  - [ ] `tests/integration/`
  - [ ] `tests/fixtures/`
  - [ ] `migrations/`
  - [ ] `logs/`
  - [ ] `uploads/` (with .gitkeep)

### Flask Application Skeleton
- [ ] Create `run.py` entry point
- [ ] Create `app/__init__.py` with app factory
- [ ] Create base configuration in `config.py`
- [ ] Test Flask app runs: `flask run`

### Database Setup
- [ ] Initialize Alembic: `alembic init migrations`
- [ ] Configure `alembic.ini` with database URL
- [ ] Configure `migrations/env.py` to use models
- [ ] Test migration: `alembic revision -m "Initial migration"`

### Template & Static Files
- [ ] Download Bulma CSS or set up CDN link
- [ ] Create `templates/base.html` base template
- [ ] Create `static/css/custom.css` for custom styles
- [ ] Test template rendering

---

## Phase 1: Core Data Management

### 1.1 University Management

#### CLI Implementation
- [ ] Create `cli/university_cli.py`
- [ ] Implement `add_university(name, slug)` function
- [ ] Implement `list_universities()` function
- [ ] Implement `get_university(id)` function
- [ ] Implement `update_university(id, **kwargs)` function
- [ ] Implement `delete_university(id)` function
- [ ] Add argument parser with `--help`
- [ ] Add input validation (required fields, unique slug)
- [ ] Add logging
- [ ] Add docstrings and type hints

#### Database
- [ ] Create `app/models/university.py` model
- [ ] Add TimestampMixin for created_at/updated_at
- [ ] Create migration: `alembic revision --autogenerate -m "Add university table"`
- [ ] Review and edit migration file
- [ ] Apply migration: `alembic upgrade head`

#### Testing
- [ ] Create `tests/unit/test_university_cli.py`
- [ ] Test add_university function
- [ ] Test list_universities function
- [ ] Test update_university function
- [ ] Test delete_university function
- [ ] Test validation (unique slug, required name)
- [ ] Run tests: `pytest tests/unit/test_university_cli.py`

#### Quality Checks & Commit
- [ ] Run linting: `ruff check --fix .`
- [ ] Run formatting: `ruff format .`
- [ ] Run type checking: `mypy cli/university_cli.py`
- [ ] Commit: `git commit -m "feat: add university management CLI"`

#### Web Interface
- [ ] Create `app/routes/universities.py` blueprint
- [ ] Implement list universities route
- [ ] Implement add university route
- [ ] Implement edit university route
- [ ] Implement delete university route
- [ ] Create `templates/universities/list.html`
- [ ] Create `templates/universities/form.html`
- [ ] Create `templates/universities/delete_confirm.html`

#### Integration Testing
- [ ] Create `tests/integration/test_university_routes.py`
- [ ] Test list route
- [ ] Test add route (GET and POST)
- [ ] Test edit route
- [ ] Test delete route
- [ ] Run integration tests: `pytest tests/integration/`

#### Final Commit
- [ ] Commit: `git commit -m "feat: add university management web interface"`

---

### 1.2 Student Management

#### CLI Implementation
- [ ] Create `cli/student_cli.py`
- [ ] Implement `add_student()` function
- [ ] Implement `list_students()` function with search/filter
- [ ] Implement `get_student()` function
- [ ] Implement `update_student()` function
- [ ] Implement `delete_student()` function
- [ ] Add email validation function
- [ ] Add student ID validation function
- [ ] Add argument parser with all fields
- [ ] Add logging
- [ ] Add comprehensive docstrings and type hints

#### Database
- [ ] Create `app/models/student.py` model
- [ ] Add unique constraints on student_id and email
- [ ] Add indexes on student_id, email, last_name
- [ ] Create migration: `alembic revision --autogenerate -m "Add student table"`
- [ ] Review migration file
- [ ] Apply migration: `alembic upgrade head`

#### Testing
- [ ] Create `tests/unit/test_student_cli.py`
- [ ] Test add_student function
- [ ] Test list_students function
- [ ] Test search functionality
- [ ] Test update_student function
- [ ] Test delete_student function
- [ ] Test email validation
- [ ] Test student ID validation
- [ ] Test unique constraints
- [ ] Run tests: `pytest tests/unit/test_student_cli.py -v`

#### Quality Checks & Commit
- [ ] Run linting: `ruff check --fix .`
- [ ] Run formatting: `ruff format .`
- [ ] Run type checking: `mypy cli/student_cli.py`
- [ ] Run all tests: `pytest`
- [ ] Commit: `git commit -m "feat: add student management CLI"`

#### Web Interface
- [ ] Create `app/routes/students.py` blueprint
- [ ] Implement list students route with search
- [ ] Implement student detail route
- [ ] Implement add student route
- [ ] Implement edit student route
- [ ] Implement delete student route
- [ ] Create `templates/students/list.html` with search form
- [ ] Create `templates/students/detail.html`
- [ ] Create `templates/students/form.html`
- [ ] Create `templates/students/delete_confirm.html`
- [ ] Add pagination to list view

#### Integration Testing
- [ ] Create `tests/integration/test_student_routes.py`
- [ ] Test list route
- [ ] Test search functionality
- [ ] Test detail route
- [ ] Test add route
- [ ] Test edit route
- [ ] Test delete route
- [ ] Test validation errors
- [ ] Run integration tests

#### Final Commit
- [ ] Commit: `git commit -m "feat: add student management web interface"`

---

### 1.3 Course Management

#### CLI Implementation
- [ ] Create `cli/course_cli.py`
- [ ] Implement `add_course()` function
- [ ] Implement `list_courses()` function with filters
- [ ] Implement `get_course()` function
- [ ] Implement `update_course()` function
- [ ] Implement `delete_course()` function
- [ ] Add semester format validation
- [ ] Add automatic slug generation from name
- [ ] Add logging and docstrings

#### Database
- [ ] Create `app/models/course.py` model
- [ ] Add foreign key to university
- [ ] Add unique constraint: (university_id, semester, slug)
- [ ] Add indexes on university_id, semester
- [ ] Create migration: `alembic revision --autogenerate -m "Add course table"`
- [ ] Apply migration: `alembic upgrade head`

#### Testing
- [ ] Create `tests/unit/test_course_cli.py`
- [ ] Test add_course function
- [ ] Test list_courses with filters
- [ ] Test semester format validation
- [ ] Test slug generation
- [ ] Test unique constraint
- [ ] Run tests: `pytest tests/unit/test_course_cli.py -v`

#### Quality Checks & Commit
- [ ] Run linting and formatting
- [ ] Run type checking: `mypy cli/course_cli.py`
- [ ] Run all tests
- [ ] Commit: `git commit -m "feat: add course management CLI"`

#### Web Interface
- [ ] Create `app/routes/courses.py` blueprint
- [ ] Implement list courses route (grouped by semester)
- [ ] Implement course detail route
- [ ] Implement add course route
- [ ] Implement edit course route
- [ ] Implement delete course route
- [ ] Create templates for courses
- [ ] Add university selection dropdown

#### Integration Testing
- [ ] Create `tests/integration/test_course_routes.py`
- [ ] Test all routes
- [ ] Test filtering and grouping
- [ ] Run integration tests

#### Final Commit
- [ ] Commit: `git commit -m "feat: add course management web interface"`

---

### 1.4 Student Enrollment

#### CLI Implementation
- [ ] Create `cli/enrollment_cli.py`
- [ ] Implement `enroll_student()` function
- [ ] Implement `list_enrollments()` function
- [ ] Implement `unenroll_student()` function
- [ ] Implement `update_enrollment_status()` function
- [ ] Add duplicate enrollment prevention
- [ ] Add validation (student exists, course exists)
- [ ] Add logging and docstrings

#### Database
- [ ] Create `app/models/enrollment.py` model
- [ ] Add foreign keys to student and course
- [ ] Add unique constraint: (student_id, course_id)
- [ ] Add indexes
- [ ] Add status enum/choices
- [ ] Create migration: `alembic revision --autogenerate -m "Add enrollment table"`
- [ ] Apply migration: `alembic upgrade head`

#### Testing
- [ ] Create `tests/unit/test_enrollment_cli.py`
- [ ] Test enroll_student function
- [ ] Test duplicate prevention
- [ ] Test unenroll_student function
- [ ] Test status transitions
- [ ] Run tests

#### Quality Checks & Commit
- [ ] Linting, formatting, type checking
- [ ] Run all tests
- [ ] Commit: `git commit -m "feat: add enrollment management CLI"`

#### Web Interface
- [ ] Create `app/routes/enrollments.py` blueprint
- [ ] Add enrollment form to student detail page
- [ ] Add enrollment form to course detail page
- [ ] Implement bulk enrollment (CSV upload)
- [ ] Create enrollment management templates

#### Integration Testing
- [ ] Create `tests/integration/test_enrollment_routes.py`
- [ ] Test enrollment workflows
- [ ] Test bulk enrollment
- [ ] Run integration tests

#### Final Commit
- [ ] Commit: `git commit -m "feat: add enrollment web interface"`

---

## Phase 2: Examination System

### 2.1 Exam Creation

#### CLI Implementation
- [ ] Create `cli/exam_cli.py`
- [ ] Implement `add_exam()` function
- [ ] Implement `list_exams()` function
- [ ] Implement `get_exam()` function
- [ ] Implement `update_exam()` function
- [ ] Implement `delete_exam()` function
- [ ] Add validation (weight 0-1, positive points, due date)
- [ ] Add logging and docstrings

#### Database
- [ ] Create `app/models/exam.py` model
- [ ] Add foreign key to course
- [ ] Add indexes
- [ ] Create migration
- [ ] Apply migration

#### Testing & Commit
- [ ] Create `tests/unit/test_exam_cli.py`
- [ ] Test all functions
- [ ] Test validations
- [ ] Linting and type checking
- [ ] Commit CLI

#### Web Interface & Integration Tests
- [ ] Create `app/routes/exams.py` blueprint
- [ ] Create exam management templates
- [ ] Add date picker for due date
- [ ] Create integration tests
- [ ] Commit web interface

---

### 2.2 Multi-Part Exams (Components)

#### CLI Implementation
- [ ] Create `cli/exam_component_cli.py`
- [ ] Implement component CRUD functions
- [ ] Add weight validation (sum to 1.0)
- [ ] Add order management

#### Database
- [ ] Create `app/models/exam_component.py` model
- [ ] Create migration
- [ ] Apply migration

#### Testing & Commit
- [ ] Create unit tests
- [ ] Test weight sum validation
- [ ] Test order management
- [ ] Commit CLI

#### Web Interface
- [ ] Add component management to exam detail page
- [ ] Add inline editing
- [ ] Add reorder functionality (drag-drop or buttons)
- [ ] Create integration tests
- [ ] Commit web interface

---

### 2.3 Submission Tracking

#### CLI Implementation
- [ ] Create `cli/submission_cli.py`
- [ ] Implement `create_submission()` function
- [ ] Implement `list_submissions()` function
- [ ] Implement `update_submission()` function
- [ ] Add points validation (≤ max_points)
- [ ] Add enrollment validation

#### Database
- [ ] Create `app/models/submission.py` model
- [ ] Add foreign keys to student, exam, component
- [ ] Add unique constraint
- [ ] Create migration
- [ ] Apply migration

#### Testing & Commit
- [ ] Create unit tests
- [ ] Test validations
- [ ] Commit CLI

#### Web Interface
- [ ] Create submission overview for exam
- [ ] Add submission table with all students
- [ ] Add bulk update functionality
- [ ] Create integration tests
- [ ] Commit web interface

---

### 2.4 Grading System

#### CLI Implementation
- [ ] Create `cli/grading_cli.py`
- [ ] Implement `calculate_grade()` function
- [ ] Implement `batch_calculate_grades()` function
- [ ] Implement grade scale configuration
- [ ] Add grade export to CSV

#### Business Logic
- [ ] Create `app/services/grading_service.py`
- [ ] Implement grade calculation algorithms
- [ ] Support German grading scale (1.0-5.0)
- [ ] Support weighted component grades
- [ ] Add configurable grade scales

#### Testing & Commit
- [ ] Create unit tests for grade calculation
- [ ] Test different grading scales
- [ ] Test weighted grades
- [ ] Commit grading system

#### Web Interface
- [ ] Create grade entry interface (table view)
- [ ] Add automatic calculation on points entry
- [ ] Add manual override option
- [ ] Add grade distribution chart (Chart.js)
- [ ] Add export to CSV/Excel
- [ ] Create integration tests
- [ ] Commit web interface

---

### 2.5 Grade Monitoring

#### CLI Implementation
- [ ] Create grade status reporting functions
- [ ] Implement missing grade detection

#### Web Interface
- [ ] Create grading dashboard
- [ ] Show ungraded submissions
- [ ] Show grading progress per course
- [ ] Add alerts for overdue grading
- [ ] Commit

---

## Phase 3: Document Management

### 3.1 File Storage System

#### CLI Implementation
- [ ] Create `cli/file_cli.py`
- [ ] Implement `upload_file()` function
- [ ] Implement `list_files()` function
- [ ] Implement directory organization function

#### Utilities
- [ ] Create `app/utils/file_manager.py`
- [ ] Implement `sanitize_filename()` function
- [ ] Implement `allowed_file()` function
- [ ] Implement `validate_file_size()` function
- [ ] Implement automatic directory creation
- [ ] Implement unique filename generation

#### Database
- [ ] Create `app/models/document.py` model
- [ ] Add file metadata fields
- [ ] Create migration
- [ ] Apply migration

#### Testing & Commit
- [ ] Create unit tests
- [ ] Test filename sanitization
- [ ] Test file validation
- [ ] Test directory structure
- [ ] Commit CLI

#### Web Interface
- [ ] Create file upload form (drag-and-drop)
- [ ] Add file browser
- [ ] Add download functionality
- [ ] Add delete functionality
- [ ] Create integration tests
- [ ] Commit web interface

---

### 3.2 Email Parser

#### CLI Implementation
- [ ] Create `cli/email_parser_cli.py`
- [ ] Implement `.mbox` file parsing
- [ ] Implement `.eml` file parsing
- [ ] Implement IMAP connection (optional)
- [ ] Implement attachment extraction

#### Business Logic
- [ ] Create `app/services/email_parser.py`
- [ ] Implement email header parsing
- [ ] Implement student matching by email
- [ ] Implement student matching by student ID in subject/body
- [ ] Implement student matching by name
- [ ] Add unmatched email flagging

#### Dependencies
- [ ] Add `imapclient` if needed: `uv add imapclient`

#### Testing & Commit
- [ ] Create test fixtures (sample emails)
- [ ] Create unit tests
- [ ] Test parsing various email formats
- [ ] Test student matching algorithms
- [ ] Commit CLI

#### Web Interface
- [ ] Create email import page
- [ ] Add email list view
- [ ] Add attachment assignment interface
- [ ] Create integration tests
- [ ] Commit web interface

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
- [ ] Create assignment functions in `cli/document_cli.py`
- [ ] Implement `assign_document()` function
- [ ] Implement `list_unassigned_documents()` function

#### Web Interface
- [ ] Create unassigned documents dashboard
- [ ] Add search and assign interface
- [ ] Add bulk assignment
- [ ] Add document preview
- [ ] Commit

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
- [ ] Enhance `templates/base.html`
- [ ] Add navigation menu
- [ ] Add breadcrumb navigation
- [ ] Style flash messages
- [ ] Add footer

#### Components
- [ ] Create `templates/components/nav.html`
- [ ] Create `templates/components/breadcrumb.html`
- [ ] Create `templates/components/pagination.html`
- [ ] Create `templates/components/table.html`
- [ ] Create `templates/components/form_field.html`
- [ ] Create `templates/components/modal.html`
- [ ] Add loading indicators

#### Styling
- [ ] Create `static/css/custom.css`
- [ ] Ensure responsive design (mobile-friendly)
- [ ] Add custom Bulma variables
- [ ] Test on different screen sizes

---

### 6.2 Dashboard

#### Implementation
- [ ] Create `app/routes/dashboard.py` blueprint
- [ ] Implement homepage dashboard
- [ ] Add statistics (students, courses, exams)
- [ ] Add recent activity feed
- [ ] Add quick actions
- [ ] Add alerts (missing grades, etc.)

#### Visualizations
- [ ] Add Chart.js: `uv add chart.js` or use CDN
- [ ] Create grade distribution chart
- [ ] Create enrollment trends chart

#### Template
- [ ] Create `templates/dashboard/index.html`
- [ ] Commit dashboard

---

### 6.3 Search & Filtering

#### Implementation
- [ ] Implement global search
- [ ] Add advanced filters to all list pages
- [ ] Add filter presets
- [ ] Add export filtered results

#### Testing
- [ ] Test search functionality
- [ ] Test filters
- [ ] Commit

---

## Documentation & Deployment

### Documentation
- [ ] Update README.md with installation instructions
- [ ] Add usage examples to README
- [ ] Document API endpoints (if created)
- [ ] Create user guide (optional)

### Testing & Quality
- [ ] Run full test suite: `pytest`
- [ ] Check test coverage: `pytest --cov=app --cov=cli`
- [ ] Ensure >80% code coverage
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
