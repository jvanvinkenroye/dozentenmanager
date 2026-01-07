# Data Model

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ University  │         │   Course    │         │   Student   │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ id (PK)     │────┐    │ id (PK)     │    ┌────│ id (PK)     │
│ name        │    │    │ name        │    │    │ first_name  │
│ slug        │    └───<│ university  │    │    │ last_name   │
│ created_at  │         │   _id (FK)  │    │    │ student_id  │
│ updated_at  │         │ semester    │    │    │ email       │
└─────────────┘         │ created_at  │    │    │ program     │
                        │ updated_at  │    │    │ created_at  │
                        └─────────────┘    │    │ updated_at  │
                               │           │    └─────────────┘
                               │           │
                        ┌──────┴───────────┴────┐
                        │    Enrollment         │
                        ├───────────────────────┤
                        │ id (PK)               │
                        │ student_id (FK)       │
                        │ course_id (FK)        │
                        │ enrollment_date       │
                        │ unenrollment_date     │
                        │ status                │
                        └───────────────────────┘
                                   │
                                   │
                        ┌──────────┴────────────┐
                        │        Exam           │
                        ├───────────────────────┤
                        │ id (PK)               │
                        │ course_id (FK)        │
                        │ name                  │
                        │ description           │
                        │ max_points            │
                        │ weight                │
                        │ due_date              │
                        │ created_at            │
                        └───────────────────────┘
                                   │
                        ┌──────────┴────────────┐
                        │    ExamComponent      │
                        ├───────────────────────┤
                        │ id (PK)               │
                        │ exam_id (FK)          │
                        │ name                  │
                        │ max_points            │
                        │ weight                │
                        │ order                 │
                        └───────────────────────┘
                                   │
                        ┌──────────┴────────────┐
                        │    Submission         │
                        ├───────────────────────┤
                        │ id (PK)               │
                        │ student_id (FK)       │
                        │ exam_id (FK)          │
                        │ component_id (FK)     │
                        │ submitted             │
                        │ submission_date       │
                        │ points                │
                        │ grade                 │
                        │ created_at            │
                        │ updated_at            │
                        └───────────────────────┘
                                   │
                        ┌──────────┴────────────┐
                        │      Document         │
                        ├───────────────────────┤
                        │ id (PK)               │
                        │ submission_id (FK)    │
                        │ filename              │
                        │ original_filename     │
                        │ file_path             │
                        │ file_type             │
                        │ file_size             │
                        │ uploaded_at           │
                        │ parsed                │
                        └───────────────────────┘

                        ┌───────────────────────┐
                        │     AuditLog          │
                        ├───────────────────────┤
                        │ id (PK)               │
                        │ table_name            │
                        │ record_id             │
                        │ action                │
                        │ old_value             │
                        │ new_value             │
                        │ changed_by            │
                        │ changed_at            │
                        └───────────────────────┘
```

## Table Definitions

### University

Represents educational institutions.

| Column     | Type         | Constraints           | Description                    |
|------------|--------------|-----------------------|--------------------------------|
| id         | INTEGER      | PRIMARY KEY           | Unique identifier              |
| name       | VARCHAR(255) | NOT NULL, UNIQUE      | Full university name           |
| slug       | VARCHAR(100) | NOT NULL, UNIQUE      | URL-friendly identifier        |
| created_at | DATETIME     | NOT NULL, DEFAULT NOW | Record creation timestamp      |
| updated_at | DATETIME     | NOT NULL, DEFAULT NOW | Record update timestamp        |

**Indexes:**
- `idx_university_slug` on `slug`

**Example:**
```sql
INSERT INTO university (name, slug) VALUES ('Technische Hochschule Köln', 'th-koeln');
```

### Course

Represents courses/lectures offered at universities.

| Column        | Type         | Constraints           | Description                    |
|---------------|--------------|-----------------------|--------------------------------|
| id            | INTEGER      | PRIMARY KEY           | Unique identifier              |
| university_id | INTEGER      | FOREIGN KEY, NOT NULL | Reference to university        |
| name          | VARCHAR(255) | NOT NULL              | Course name                    |
| semester      | VARCHAR(50)  | NOT NULL              | Semester (e.g., "2023_SoSe")   |
| description   | TEXT         |                       | Course description             |
| slug          | VARCHAR(100) | NOT NULL              | URL-friendly identifier        |
| created_at    | DATETIME     | NOT NULL, DEFAULT NOW | Record creation timestamp      |
| updated_at    | DATETIME     | NOT NULL, DEFAULT NOW | Record update timestamp        |

**Indexes:**
- `idx_course_university` on `university_id`
- `idx_course_semester` on `semester`
- `idx_course_slug` on `slug`

**Unique Constraint:**
- `(university_id, semester, slug)` - No duplicate courses per semester

**Example:**
```sql
INSERT INTO course (university_id, name, semester, slug)
VALUES (1, 'Einführung in Statistik', '2023_SoSe', 'einfuehrung-statistik');
```

### Student

Represents students enrolled in the system.

| Column     | Type         | Constraints           | Description                    |
|------------|--------------|-----------------------|--------------------------------|
| id         | INTEGER      | PRIMARY KEY           | Unique identifier              |
| first_name | VARCHAR(100) | NOT NULL              | Student's first name           |
| last_name  | VARCHAR(100) | NOT NULL              | Student's last name            |
| student_id | VARCHAR(50)  | NOT NULL, UNIQUE      | Matriculation number           |
| email      | VARCHAR(255) | NOT NULL, UNIQUE      | Student email address          |
| program    | VARCHAR(255) |                       | Study program                  |
| created_at | DATETIME     | NOT NULL, DEFAULT NOW | Record creation timestamp      |
| updated_at | DATETIME     | NOT NULL, DEFAULT NOW | Record update timestamp        |

**Indexes:**
- `idx_student_student_id` on `student_id`
- `idx_student_email` on `email`
- `idx_student_last_name` on `last_name`

**Example:**
```sql
INSERT INTO student (first_name, last_name, student_id, email, program)
VALUES ('Mike', 'Mueller', '12345678', 'mike.mueller@example.com', 'Computer Science B.Sc.');
```

### Enrollment

Many-to-many relationship between students and courses.

| Column              | Type         | Constraints           | Description                    |
|---------------------|--------------|-----------------------|--------------------------------|
| id                  | INTEGER      | PRIMARY KEY           | Unique identifier              |
| student_id          | INTEGER      | FOREIGN KEY, NOT NULL | Reference to student           |
| course_id           | INTEGER      | FOREIGN KEY, NOT NULL | Reference to course            |
| enrollment_date     | DATE         | NOT NULL, DEFAULT NOW | When student enrolled          |
| unenrollment_date   | DATE         |                       | When student unenrolled        |
| status              | VARCHAR(20)  | NOT NULL              | active, completed, dropped     |

**Indexes:**
- `idx_enrollment_student` on `student_id`
- `idx_enrollment_course` on `course_id`
- `idx_enrollment_status` on `status`

**Unique Constraint:**
- `(student_id, course_id)` - Student can only enroll once per course

**Example:**
```sql
INSERT INTO enrollment (student_id, course_id, status)
VALUES (1, 1, 'active');
```

### Exam

Represents exams or assessments for courses.

| Column      | Type         | Constraints           | Description                    |
|-------------|--------------|-----------------------|--------------------------------|
| id          | INTEGER      | PRIMARY KEY           | Unique identifier              |
| course_id   | INTEGER      | FOREIGN KEY, NOT NULL | Reference to course            |
| name        | VARCHAR(255) | NOT NULL              | Exam name                      |
| description | TEXT         |                       | Exam description               |
| max_points  | DECIMAL(5,2) | NOT NULL              | Maximum achievable points      |
| weight      | DECIMAL(3,2) |                       | Weight for final grade (0-1)   |
| due_date    | DATETIME     |                       | Submission deadline            |
| created_at  | DATETIME     | NOT NULL, DEFAULT NOW | Record creation timestamp      |
| updated_at  | DATETIME     | NOT NULL, DEFAULT NOW | Record update timestamp        |

**Indexes:**
- `idx_exam_course` on `course_id`
- `idx_exam_due_date` on `due_date`

**Example:**
```sql
INSERT INTO exam (course_id, name, max_points, weight, due_date)
VALUES (1, 'Final Exam', 100.00, 0.60, '2023-07-15 12:00:00');
```

### ExamComponent

Represents parts of an exam (for multi-part exams).

| Column     | Type         | Constraints           | Description                    |
|------------|--------------|-----------------------|--------------------------------|
| id         | INTEGER      | PRIMARY KEY           | Unique identifier              |
| exam_id    | INTEGER      | FOREIGN KEY, NOT NULL | Reference to exam              |
| name       | VARCHAR(255) | NOT NULL              | Component name                 |
| max_points | DECIMAL(5,2) | NOT NULL              | Maximum points for this part   |
| weight     | DECIMAL(3,2) |                       | Weight within exam (0-1)       |
| order      | INTEGER      | NOT NULL, DEFAULT 0   | Display/processing order       |

**Indexes:**
- `idx_component_exam` on `exam_id`
- `idx_component_order` on `(exam_id, order)`

**Example:**
```sql
INSERT INTO exam_component (exam_id, name, max_points, weight, order)
VALUES (1, 'Multiple Choice', 40.00, 0.40, 1);
```

### Submission

Tracks student submissions and grades.

| Column          | Type         | Constraints           | Description                    |
|-----------------|--------------|-----------------------|--------------------------------|
| id              | INTEGER      | PRIMARY KEY           | Unique identifier              |
| student_id      | INTEGER      | FOREIGN KEY, NOT NULL | Reference to student           |
| exam_id         | INTEGER      | FOREIGN KEY, NOT NULL | Reference to exam              |
| component_id    | INTEGER      | FOREIGN KEY           | Reference to component (null if whole exam) |
| submitted       | BOOLEAN      | NOT NULL, DEFAULT 0   | Whether submitted              |
| submission_date | DATETIME     |                       | When submitted                 |
| points          | DECIMAL(5,2) |                       | Points achieved                |
| grade           | VARCHAR(10)  |                       | Final grade (e.g., "1.0", "B+") |
| notes           | TEXT         |                       | Grading notes                  |
| created_at      | DATETIME     | NOT NULL, DEFAULT NOW | Record creation timestamp      |
| updated_at      | DATETIME     | NOT NULL, DEFAULT NOW | Record update timestamp        |

**Indexes:**
- `idx_submission_student` on `student_id`
- `idx_submission_exam` on `exam_id`
- `idx_submission_component` on `component_id`
- `idx_submission_submitted` on `submitted`

**Unique Constraint:**
- `(student_id, exam_id, component_id)` - One submission per student per component

**Example:**
```sql
INSERT INTO submission (student_id, exam_id, submitted, submission_date, points, grade)
VALUES (1, 1, 1, '2023-07-14 10:30:00', 85.00, '1.7');
```

### Document

Stores information about uploaded documents.

| Column            | Type         | Constraints           | Description                    |
|-------------------|--------------|-----------------------|--------------------------------|
| id                | INTEGER      | PRIMARY KEY           | Unique identifier              |
| submission_id     | INTEGER      | FOREIGN KEY           | Reference to submission (nullable for unassigned) |
| filename          | VARCHAR(255) | NOT NULL              | Stored filename (sanitized)    |
| original_filename | VARCHAR(255) | NOT NULL              | Original uploaded filename     |
| file_path         | VARCHAR(500) | NOT NULL              | Full path to file              |
| file_type         | VARCHAR(50)  | NOT NULL              | MIME type                      |
| file_size         | INTEGER      | NOT NULL              | File size in bytes             |
| uploaded_at       | DATETIME     | NOT NULL, DEFAULT NOW | Upload timestamp               |
| parsed            | BOOLEAN      | NOT NULL, DEFAULT 0   | Whether content has been parsed |
| parsed_content    | TEXT         |                       | Extracted text content         |

**Indexes:**
- `idx_document_submission` on `submission_id`
- `idx_document_uploaded` on `uploaded_at`
- `idx_document_parsed` on `parsed`

**Example:**
```sql
INSERT INTO document (submission_id, filename, original_filename, file_path, file_type, file_size)
VALUES (1, 'abc123.pdf', 'my_exam.pdf', 'th-koeln/2023_SoSe/statistik/MuellerMike/abc123.pdf', 'application/pdf', 245678);
```

### AuditLog

Comprehensive audit trail for all important changes.

| Column      | Type         | Constraints           | Description                    |
|-------------|--------------|-----------------------|--------------------------------|
| id          | INTEGER      | PRIMARY KEY           | Unique identifier              |
| table_name  | VARCHAR(50)  | NOT NULL              | Name of affected table         |
| record_id   | INTEGER      | NOT NULL              | ID of affected record          |
| action      | VARCHAR(20)  | NOT NULL              | INSERT, UPDATE, DELETE         |
| field_name  | VARCHAR(50)  |                       | Changed field (UPDATE only)    |
| old_value   | TEXT         |                       | Previous value                 |
| new_value   | TEXT         |                       | New value                      |
| changed_by  | VARCHAR(255) |                       | User who made change (future)  |
| changed_at  | DATETIME     | NOT NULL, DEFAULT NOW | When change occurred           |
| ip_address  | VARCHAR(45)  |                       | IP address of requester        |

**Indexes:**
- `idx_audit_table_record` on `(table_name, record_id)`
- `idx_audit_changed_at` on `changed_at`
- `idx_audit_action` on `action`

**Example:**
```sql
INSERT INTO audit_log (table_name, record_id, action, field_name, old_value, new_value, changed_by)
VALUES ('submission', 1, 'UPDATE', 'grade', '2.0', '1.7', 'admin@example.com');
```

## SQLAlchemy Models

### Base Configuration

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime, timezone

Base = declarative_base()

class TimestampMixin:
    """Mixin for adding timezone-aware timestamp columns"""
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

### Example Model Implementation

```python
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Decimal, Date, Text
from sqlalchemy.orm import relationship

class Student(Base, TimestampMixin):
    __tablename__ = 'student'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    program = Column(String(255))

    # Relationships
    enrollments = relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    submissions = relationship('Submission', back_populates='student', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.first_name} {self.last_name}', student_id='{self.student_id}')>"
```

## Data Validation Rules

### Student
- Email must be valid format
- Student ID must be unique and alphanumeric
- First and last names required

### Enrollment
- Cannot enroll in same course twice (unless previously unenrolled)
- Status must be one of: 'active', 'completed', 'dropped'
- Enrollment date cannot be in the future

### Submission
- Points cannot exceed exam max_points
- Submission date cannot be before exam creation
- Grade conversion based on configurable scale

### Document
- File type must be in allowed list (PDF, DOC, DOCX, TXT)
- File size must not exceed maximum (e.g., 10MB)
- Filename sanitization to prevent path traversal

## Grade Conversion Scale

Configurable grade conversion (German grading system example):

| Points (%)  | Grade |
|-------------|-------|
| 95-100      | 1.0   |
| 90-94       | 1.3   |
| 85-89       | 1.7   |
| 80-84       | 2.0   |
| 75-79       | 2.3   |
| 70-74       | 2.7   |
| 65-69       | 3.0   |
| 60-64       | 3.3   |
| 55-59       | 3.7   |
| 50-54       | 4.0   |
| 0-49        | 5.0   |

This should be configurable per course or university.

## Migration Strategy

Use Alembic for database migrations:

```bash
# Initialize migrations
alembic init migrations

# Create a new migration
alembic revision --autogenerate -m "Add audit_log table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```
