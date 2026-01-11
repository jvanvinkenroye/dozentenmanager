# Architecture

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Web Framework**: Flask
- **Package Manager**: UV (fast Python package manager)
- **Database**: SQLite
  - Simple setup, no external database server required
  - Suitable for small to medium-sized deployments
  - File-based, easy to backup

### Frontend
- **CSS Framework**: Bulma CSS
  - Modern, responsive, flexbox-based
  - No JavaScript dependencies
  - Clean and professional UI components

### Development Tools
- **Linting**: Ruff (fast Python linter and formatter)
- **Type Checking**: mypy
- **Testing**: pytest
- **Virtual Environment**: UV venv

## System Architecture

```
┌─────────────────────────────────────────┐
│           Web Browser (Client)          │
└────────────────┬────────────────────────┘
                 │ HTTP/HTTPS
                 ▼
┌─────────────────────────────────────────┐
│         Flask Application Server        │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │      Web Routes & Views         │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │      Business Logic Layer       │   │
│  │      (Service Layer)            │   │
│  │  - UniversityService            │   │
│  │  - StudentService               │   │
│  │  - CourseService                │   │
│  │  - EnrollmentService            │   │
│  │  - ExamService                  │   │
│  │  - Grading System               │   │
│  │  - Document Processing          │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │      Data Access Layer (ORM)    │   │
│  │      SQLAlchemy                 │   │
│  └──────────────┬──────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          SQLite Database                │
└─────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      File System Storage                │
│  Hochschule/Semester/Course/Student/    │
└─────────────────────────────────────────┘
```

## Application Structure

```
dozentenmanager/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models/               # Database models
│   │   ├── __init__.py
│   │   ├── student.py
│   │   ├── university.py
│   │   ├── course.py
│   │   ├── exam.py
│   │   └── grade.py
│   ├── routes/               # Flask blueprints
│   │   ├── __init__.py
│   │   ├── students.py
│   │   ├── courses.py
│   │   ├── exams.py
│   │   └── documents.py
│   ├── services/             # Business logic layer
│   │   ├── __init__.py
│   │   ├── base_service.py       # Base service with common DB operations
│   │   ├── university_service.py # University management
│   │   ├── student_service.py    # Student management
│   │   ├── course_service.py     # Course management
│   │   ├── enrollment_service.py # Enrollment management
│   │   ├── exam_service.py       # Exam management
│   │   ├── grading_service.py    # Grading logic
│   │   ├── email_parser.py       # Email parsing
│   │   └── document_parser.py    # Document processing
│   ├── utils/                # Utilities
│   │   ├── __init__.py
│   │   ├── file_manager.py
│   │   └── validators.py
│   ├── templates/            # Jinja2 templates
│   │   ├── base.html
│   │   ├── students/
│   │   ├── courses/
│   │   └── exams/
│   └── static/               # CSS, JS, images
│       ├── css/
│       ├── js/
│       └── images/
├── cli/                      # CLI tools
│   ├── __init__.py
│   ├── student_cli.py
│   ├── import_export.py
│   └── parser_cli.py
├── tests/                    # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── migrations/               # Database migrations (Alembic)
├── uploads/                  # User-uploaded files
│   └── [organized by structure]
├── config.py                 # Configuration management
├── pyproject.toml            # Project dependencies
├── .env.example              # Environment variables template
└── run.py                    # Application entry point
```

## Key Design Patterns

### Factory Pattern
- Flask app creation using application factory pattern
- Enables testing with different configurations
- Clean separation of configuration and initialization

### Service Layer Pattern
- **Status**: ✅ Fully Implemented (Issue #11)
- Business logic encapsulated in dedicated service classes
- All services inherit from BaseService with common database operations
- Services raise exceptions (ValueError, IntegrityError) for error handling
- CLI tools and web routes consume services and convert exceptions appropriately
- Clean separation of concerns: Models → Services → Routes/CLI
- Makes testing easier with service-level mocking
- **Implemented Services**:
  - `UniversityService`: University CRUD operations
  - `StudentService`: Student management with validation
  - `CourseService`: Course management with slug generation
  - `EnrollmentService`: Student enrollment and status management
  - `ExamService`: Exam management with validation
- Data access abstracted through service layer
- Business logic separated from data persistence
- Easier to test and maintain

### Blueprint Pattern
- Modular route organization using Flask blueprints
- Each major feature area has its own blueprint
- Promotes code reusability

## Database Layer

### ORM: SQLAlchemy
- Object-relational mapping for database interactions
- Type-safe database queries
- Automatic relationship management
- Migration support via Alembic

### Connection Handling
- Connection pooling for efficiency
- Transaction management
- Automatic rollback on errors

## File Storage

### Organization Strategy
Files organized hierarchically:
```
uploads/
└── {university_slug}/
    └── {semester}/
        └── {course_slug}/
            └── {lastname}{firstname}/
                ├── assignment1.pdf
                ├── exam_final.pdf
                └── metadata.json
```

### File Naming
- Sanitize filenames to prevent path traversal
- Preserve original filename in metadata
- Add timestamp or hash for uniqueness if needed

## Security Considerations

### Input Validation
- All user inputs validated before processing
- Email address validation
- File type validation for uploads
- SQL injection prevention via ORM

### File Upload Security
- Whitelist allowed file extensions
- Virus scanning integration point
- File size limits
- Secure filename handling

### Authentication & Authorization
- User authentication system (future enhancement)
- Role-based access control (RBAC)
- Session management

### Data Protection
- Password hashing (when user auth added)
- Secure session cookies
- CSRF protection
- SQL injection prevention

## Performance Considerations

### Database Optimization
- Proper indexing on foreign keys and frequently queried fields
- Query optimization with SQLAlchemy lazy loading
- Pagination for large result sets

### Caching Strategy
- Static file caching
- Template fragment caching
- Database query caching for read-heavy operations

### File Processing
- Background task queue for large file processing (Celery/RQ future)
- Streaming for large file downloads
- Thumbnail generation for images

## Scalability Path

### Current Design (Phase 1)
- Single SQLite database
- Local file storage
- Single-process Flask server

### Future Scaling Options (Phase 2+)
- PostgreSQL/MySQL for concurrent writes
- Cloud storage (S3, etc.) for files
- Redis for session storage and caching
- Background task processing (Celery)
- Containerization (Docker)
- Horizontal scaling with load balancer

## Monitoring & Logging

### Application Logging
- Structured logging with Python logging module
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Separate log files for different components
- Rotation and retention policies

### Audit Trail
- All grade changes logged with timestamp and user
- Student enrollment/unenrollment tracked
- Document upload tracking
- Database-backed audit log

### Error Tracking
- Exception logging
- Email notifications for critical errors (optional)
- Error pages with helpful messages

## Development vs. Production

### Development Configuration
- Debug mode enabled
- Detailed error pages
- Auto-reload on code changes
- SQLite database in project directory

### Production Configuration
- Debug mode disabled
- Generic error pages
- Proper logging setup
- Environment-based configuration
- Database backups
- HTTPS enforcement
