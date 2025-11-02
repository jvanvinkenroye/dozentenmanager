# Features & Implementation Roadmap

## Feature Overview

This document breaks down all features from the concept into implementable tasks, organized by priority and dependencies.

## Phase 1: Core Data Management (Foundation)

### 1.1 University Management

**Priority:** HIGH
**Dependencies:** None
**Complexity:** LOW

**CLI Implementation:**
- [ ] `university add --name "TH Köln" --slug "th-koeln"`
- [ ] `university list`
- [ ] `university update <id> --name "New Name"`
- [ ] `university delete <id>`

**Web Interface:**
- [ ] University list page
- [ ] Add university form
- [ ] Edit university form
- [ ] Delete confirmation

**Database:**
- [ ] University model
- [ ] Migration for university table

**Tests:**
- [ ] Unit tests for university CRUD operations
- [ ] Validation tests (unique slug, required fields)
- [ ] Integration tests for web routes

---

### 1.2 Student Management

**Priority:** HIGH
**Dependencies:** None
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `student add --first-name "Max" --last-name "Mustermann" --student-id "12345678" --email "max@example.com" --program "Computer Science"`
- [ ] `student list [--search "name"] [--program "CS"]`
- [ ] `student show <student-id>`
- [ ] `student update <student-id> --email "new@example.com"`
- [ ] `student delete <student-id>`

**Web Interface:**
- [ ] Student list page with search/filter
- [ ] Student detail page
- [ ] Add student form with validation
- [ ] Edit student form
- [ ] Delete confirmation with cascade warning

**Business Logic:**
- [ ] Email validation (format check, uniqueness)
- [ ] Student ID validation (format, uniqueness)
- [ ] Name validation (required, length limits)

**Database:**
- [ ] Student model
- [ ] Migration for student table
- [ ] Indexes on student_id, email, last_name

**Tests:**
- [ ] Unit tests for CRUD operations
- [ ] Validation tests (email format, unique constraints)
- [ ] Search functionality tests
- [ ] Integration tests for web routes

---

### 1.3 Course Management

**Priority:** HIGH
**Dependencies:** University Management
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `course add --university-id 1 --name "Einführung Statistik" --semester "2023_SoSe"`
- [ ] `course list [--university-id 1] [--semester "2023_SoSe"]`
- [ ] `course show <course-id>`
- [ ] `course update <course-id> --name "New Name"`
- [ ] `course delete <course-id>`

**Web Interface:**
- [ ] Course list page (grouped by university/semester)
- [ ] Course detail page showing enrolled students
- [ ] Add course form with university selection
- [ ] Edit course form
- [ ] Delete confirmation

**Business Logic:**
- [ ] Semester format validation (e.g., "2023_SoSe", "2024_WiSe")
- [ ] Unique constraint: university + semester + slug
- [ ] Automatic slug generation from name

**Database:**
- [ ] Course model
- [ ] Migration for course table
- [ ] Foreign key to university
- [ ] Indexes on university_id, semester

**Tests:**
- [ ] CRUD operation tests
- [ ] Semester format validation
- [ ] Unique constraint tests
- [ ] Filter/search tests

---

### 1.4 Student Enrollment

**Priority:** HIGH
**Dependencies:** Student Management, Course Management
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `enrollment add --student-id "12345678" --course-id 1`
- [ ] `enrollment list --course-id 1`
- [ ] `enrollment list --student-id "12345678"`
- [ ] `enrollment remove --student-id "12345678" --course-id 1`
- [ ] `enrollment status --student-id "12345678" --course-id 1 --status "dropped"`

**Web Interface:**
- [ ] Enroll student in course (from student detail page)
- [ ] Enroll student in course (from course detail page)
- [ ] Bulk enrollment (upload CSV)
- [ ] Unenroll student with date tracking
- [ ] Update enrollment status

**Business Logic:**
- [ ] Prevent duplicate enrollments (unless previously unenrolled)
- [ ] Validate status transitions
- [ ] Set enrollment date automatically
- [ ] Set unenrollment date when status changed to dropped

**Database:**
- [ ] Enrollment model
- [ ] Migration for enrollment table
- [ ] Foreign keys to student and course
- [ ] Unique constraint on (student_id, course_id)
- [ ] Indexes on student_id, course_id, status

**Tests:**
- [ ] Enrollment creation tests
- [ ] Duplicate enrollment prevention
- [ ] Status transition tests
- [ ] Date tracking tests

---

## Phase 2: Examination System

### 2.1 Exam Creation

**Priority:** HIGH
**Dependencies:** Course Management
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `exam add --course-id 1 --name "Final Exam" --max-points 100 --weight 0.6 --due-date "2023-07-15"`
- [ ] `exam list --course-id 1`
- [ ] `exam show <exam-id>`
- [ ] `exam update <exam-id> --max-points 120`
- [ ] `exam delete <exam-id>`

**Web Interface:**
- [ ] Exam list page (grouped by course)
- [ ] Add exam form with date picker
- [ ] Edit exam form
- [ ] Delete confirmation (warn about existing submissions)

**Business Logic:**
- [ ] Weight validation (0-1 range)
- [ ] Max points validation (positive number)
- [ ] Due date validation (not in past when creating)

**Database:**
- [ ] Exam model
- [ ] Migration for exam table
- [ ] Foreign key to course

**Tests:**
- [ ] CRUD operation tests
- [ ] Validation tests (weight range, positive points)
- [ ] Due date tests

---

### 2.2 Multi-Part Exams (Components)

**Priority:** MEDIUM
**Dependencies:** Exam Creation
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `exam-component add --exam-id 1 --name "Multiple Choice" --max-points 40 --weight 0.4 --order 1`
- [ ] `exam-component list --exam-id 1`
- [ ] `exam-component update <component-id> --max-points 50`
- [ ] `exam-component delete <component-id>`

**Web Interface:**
- [ ] Component management on exam detail page
- [ ] Add/edit components inline
- [ ] Reorder components (drag-and-drop or up/down buttons)
- [ ] Visual breakdown of exam structure

**Business Logic:**
- [ ] Component weights should sum to 1.0 for an exam
- [ ] Component max_points can sum to different than exam max_points
- [ ] Order management (automatic or manual)

**Database:**
- [ ] ExamComponent model
- [ ] Migration for exam_component table
- [ ] Foreign key to exam
- [ ] Index on (exam_id, order)

**Tests:**
- [ ] Component CRUD tests
- [ ] Weight sum validation
- [ ] Order management tests

---

### 2.3 Submission Tracking

**Priority:** HIGH
**Dependencies:** Exam Creation, Student Enrollment
**Complexity:** HIGH

**CLI Implementation:**
- [ ] `submission create --student-id "12345678" --exam-id 1 --submitted true --submission-date "2023-07-14"`
- [ ] `submission list --exam-id 1 [--submitted false]`
- [ ] `submission list --student-id "12345678"`
- [ ] `submission update <submission-id> --points 85 --grade "1.7"`
- [ ] `submission show <submission-id>`

**Web Interface:**
- [ ] Submission overview for exam (table of all students)
- [ ] Mark as submitted/not submitted (checkbox)
- [ ] Bulk update submission status
- [ ] Grade entry form (points → automatic grade calculation)
- [ ] Student's submission history

**Business Logic:**
- [ ] Validate points ≤ max_points
- [ ] Automatic grade calculation from points
- [ ] Track submission date
- [ ] Only allow submissions for enrolled students
- [ ] Handle whole exam vs. component submissions

**Database:**
- [ ] Submission model
- [ ] Migration for submission table
- [ ] Foreign keys to student, exam, component (nullable)
- [ ] Unique constraint on (student_id, exam_id, component_id)
- [ ] Indexes on student_id, exam_id, submitted

**Tests:**
- [ ] Submission creation tests
- [ ] Points validation tests
- [ ] Grade calculation tests
- [ ] Enrollment validation tests
- [ ] Component vs. whole exam tests

---

### 2.4 Grading System

**Priority:** HIGH
**Dependencies:** Submission Tracking
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `grade calculate --submission-id 1`
- [ ] `grade batch-calculate --exam-id 1`
- [ ] `grade config --set-scale [scale-json]`
- [ ] `grade export --course-id 1 --format csv`

**Web Interface:**
- [ ] Grade entry interface (table view)
- [ ] Automatic grade calculation on points entry
- [ ] Manual grade override option
- [ ] Grade distribution visualization (histogram)
- [ ] Export grades to CSV/Excel

**Business Logic:**
- [ ] Configurable grading scale (percentage → grade)
- [ ] Support for different grading systems (German 1-5, A-F, etc.)
- [ ] Calculate final grade from weighted components
- [ ] Grade change detection for audit log

**Database:**
- [ ] GradeScale model (optional, for configurable scales)
- [ ] Submission model already has grade field

**Tests:**
- [ ] Grade calculation tests for different scales
- [ ] Weighted grade calculation
- [ ] Export format tests

---

### 2.5 Grade Monitoring

**Priority:** MEDIUM
**Dependencies:** Grading System
**Complexity:** LOW

**CLI Implementation:**
- [ ] `grade status --exam-id 1`
- [ ] `grade missing --course-id 1`

**Web Interface:**
- [ ] Dashboard showing grading progress
- [ ] List of exams with ungraded submissions
- [ ] Alerts for overdue grading
- [ ] Grading statistics per course

**Business Logic:**
- [ ] Identify submissions with points but no grade
- [ ] Identify submitted work with no points
- [ ] Calculate completion percentage

**Tests:**
- [ ] Status calculation tests
- [ ] Missing grade identification

---

## Phase 3: Document Management

### 3.1 File Storage System

**Priority:** HIGH
**Dependencies:** Student Management, Course Management
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `file upload --student-id "12345678" --course-id 1 --file "exam.pdf"`
- [ ] `file list --student-id "12345678" --course-id 1`
- [ ] `file organize` (organize existing files into proper structure)

**Web Interface:**
- [ ] File upload form (drag-and-drop)
- [ ] File browser for student/course
- [ ] Download file
- [ ] Delete file

**Business Logic:**
- [ ] Filename sanitization (prevent path traversal)
- [ ] File type validation (whitelist)
- [ ] File size limits
- [ ] Automatic directory creation: `university/semester/course/LastnameFirstname/`
- [ ] Unique filename generation (if duplicate)
- [ ] Store metadata (original filename, upload date, file size)

**Database:**
- [ ] Document model
- [ ] Migration for document table
- [ ] Foreign key to submission (nullable for unassigned)

**File System:**
- [ ] Create upload directory structure
- [ ] Implement secure path handling
- [ ] Add cleanup for orphaned files

**Tests:**
- [ ] File upload tests
- [ ] Filename sanitization tests
- [ ] Directory creation tests
- [ ] File type validation tests
- [ ] Size limit tests

---

### 3.2 Email Parser

**Priority:** MEDIUM
**Dependencies:** File Storage System
**Complexity:** HIGH

**CLI Implementation:**
- [ ] `email parse --mbox "inbox.mbox"`
- [ ] `email parse --imap --server "imap.gmail.com" --user "user@example.com"`
- [ ] `email extract-attachments --email-file "message.eml"`

**Web Interface:**
- [ ] Email import page (upload .mbox or .eml files)
- [ ] Email list with attachment indicators
- [ ] Attachment assignment interface (if auto-match fails)
- [ ] Preview email content

**Business Logic:**
- [ ] Parse email headers (From, Subject, Date)
- [ ] Extract attachments
- [ ] Attempt automatic student matching:
  - By email address
  - By student ID in subject/body
  - By name in subject/body
- [ ] Flag unmatched emails for manual review
- [ ] Prevent duplicate imports

**Libraries:**
- [ ] `email` (standard library for parsing)
- [ ] `mailbox` (standard library for mbox)
- [ ] `imapclient` (for IMAP access)

**Database:**
- [ ] EmailMessage model (optional, for tracking)
- [ ] Link documents to students

**Tests:**
- [ ] Email parsing tests (various formats)
- [ ] Attachment extraction tests
- [ ] Student matching tests (various patterns)
- [ ] Duplicate prevention tests

---

### 3.3 Document Parser (PDF/Word)

**Priority:** MEDIUM
**Dependencies:** File Storage System
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `document parse --file "submission.pdf"`
- [ ] `document extract-text --file "document.docx"`
- [ ] `document batch-parse --directory "uploads/"`

**Web Interface:**
- [ ] Document viewer with extracted text
- [ ] Manual text correction interface
- [ ] Automatic student matching from content
- [ ] Mark document as parsed

**Business Logic:**
- [ ] Extract text from PDF (using PyPDF2 or pdfplumber)
- [ ] Extract text from Word (using python-docx)
- [ ] Attempt to find student ID in text
- [ ] Attempt to find student name in text
- [ ] Store extracted text for searching
- [ ] Flag documents that couldn't be parsed

**Libraries:**
- [ ] `PyPDF2` or `pdfplumber` for PDF
- [ ] `python-docx` for Word documents
- [ ] `textract` (comprehensive option for multiple formats)

**Database:**
- [ ] Add `parsed` and `parsed_content` fields to Document model

**Tests:**
- [ ] PDF text extraction tests
- [ ] Word text extraction tests
- [ ] Student ID detection tests
- [ ] Name detection tests

---

### 3.4 Manual Document Assignment

**Priority:** MEDIUM
**Dependencies:** Email Parser, Document Parser
**Complexity:** LOW

**CLI Implementation:**
- [ ] `document assign --document-id 1 --student-id "12345678" --submission-id 1`
- [ ] `document unassigned` (list unassigned documents)

**Web Interface:**
- [ ] Unassigned documents dashboard
- [ ] Search and assign to student
- [ ] Bulk assignment interface
- [ ] Document preview before assignment

**Business Logic:**
- [ ] Link document to submission
- [ ] Update document metadata
- [ ] Move file if needed

**Tests:**
- [ ] Assignment tests
- [ ] Unassigned document listing
- [ ] Bulk assignment tests

---

## Phase 4: Import/Export

### 4.1 Student Import

**Priority:** MEDIUM
**Dependencies:** Student Management
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `student import --file "students.csv"`
- [ ] `student import --file "students.xlsx"`
- [ ] `student import --file "students.json"`

**Web Interface:**
- [ ] Upload CSV/Excel file
- [ ] Column mapping interface
- [ ] Preview import data
- [ ] Import with validation and error reporting

**Business Logic:**
- [ ] Parse CSV, Excel (xlsx), JSON
- [ ] Flexible column mapping
- [ ] Validate data (email format, unique student IDs)
- [ ] Batch insert with transaction
- [ ] Error handling (skip invalid rows or abort all)
- [ ] Report summary (imported, skipped, errors)

**Libraries:**
- [ ] `csv` (standard library)
- [ ] `openpyxl` for Excel
- [ ] `pandas` (optional, for advanced parsing)

**Tests:**
- [ ] CSV import tests
- [ ] Excel import tests
- [ ] JSON import tests
- [ ] Validation tests
- [ ] Error handling tests

---

### 4.2 Student Export

**Priority:** LOW
**Dependencies:** Student Management
**Complexity:** LOW

**CLI Implementation:**
- [ ] `student export --format csv --output "students.csv"`
- [ ] `student export --format xlsx --output "students.xlsx"`
- [ ] `student export --format json --output "students.json"`
- [ ] `student export --course-id 1` (export enrolled students)

**Web Interface:**
- [ ] Export button on student list page
- [ ] Format selection (CSV, Excel, JSON)
- [ ] Filter options (course, program, etc.)
- [ ] Download generated file

**Business Logic:**
- [ ] Generate CSV with proper escaping
- [ ] Generate Excel with formatting
- [ ] Generate JSON with proper structure
- [ ] Include all relevant fields

**Tests:**
- [ ] CSV export tests
- [ ] Excel export tests
- [ ] JSON export tests
- [ ] Filter tests

---

### 4.3 Grade Export

**Priority:** MEDIUM
**Dependencies:** Grading System
**Complexity:** MEDIUM

**CLI Implementation:**
- [ ] `grade export --course-id 1 --format csv`
- [ ] `grade export --exam-id 1 --format xlsx`

**Web Interface:**
- [ ] Export grades button on course/exam pages
- [ ] Format selection
- [ ] Include submission status, points, grades
- [ ] Custom column selection

**Business Logic:**
- [ ] Generate grade report with student info
- [ ] Include calculated statistics (average, median, distribution)
- [ ] Format for different systems (e.g., university import formats)

**Tests:**
- [ ] Export format tests
- [ ] Statistics calculation tests

---

## Phase 5: Audit & Logging

### 5.1 Audit Log System

**Priority:** HIGH
**Dependencies:** All CRUD operations
**Complexity:** MEDIUM

**Implementation:**
- [ ] Create audit log model
- [ ] Implement audit decorator for model changes
- [ ] Track INSERT, UPDATE, DELETE operations
- [ ] Store old and new values (JSON)
- [ ] Capture user information (when authentication added)
- [ ] Capture IP address

**CLI Implementation:**
- [ ] `audit log --table student --record-id 1`
- [ ] `audit log --action UPDATE --since "2023-07-01"`
- [ ] `audit search --field "grade" --old-value "2.0"`

**Web Interface:**
- [ ] Audit log viewer (filterable table)
- [ ] Timeline view for specific record
- [ ] Grade change history (special view)
- [ ] Export audit log

**Business Logic:**
- [ ] SQLAlchemy event listeners for automatic logging
- [ ] Efficient storage (JSONB for PostgreSQL, TEXT for SQLite)
- [ ] Retention policy (archive old logs)

**Database:**
- [ ] AuditLog model
- [ ] Migration for audit_log table
- [ ] Indexes on table_name, record_id, changed_at

**Tests:**
- [ ] Automatic logging tests
- [ ] Query and filter tests
- [ ] Retention policy tests

---

### 5.2 Grade Change Tracking

**Priority:** HIGH
**Dependencies:** Audit Log System, Grading System
**Complexity:** LOW

**CLI Implementation:**
- [ ] `grade history --submission-id 1`
- [ ] `grade changes --course-id 1 --since "2023-07-01"`

**Web Interface:**
- [ ] Grade change history on submission detail
- [ ] Recent grade changes dashboard
- [ ] Notification for grade changes (optional)

**Business Logic:**
- [ ] Filter audit log for grade field
- [ ] Display old → new value clearly
- [ ] Show timestamp and user

**Tests:**
- [ ] Grade change tracking tests
- [ ] History display tests

---

## Phase 6: Web Interface Polish

### 6.1 UI Components (Bulma CSS)

**Priority:** MEDIUM
**Dependencies:** Basic Flask routes
**Complexity:** MEDIUM

**Tasks:**
- [ ] Create base template with Bulma CSS
- [ ] Navigation menu component
- [ ] Breadcrumb navigation
- [ ] Flash message styling
- [ ] Form styling (consistent inputs, labels, buttons)
- [ ] Table styling with sorting
- [ ] Pagination component
- [ ] Modal dialogs for confirmations
- [ ] Loading indicators
- [ ] Responsive design (mobile-friendly)

**Templates:**
- [ ] `templates/base.html`
- [ ] `templates/components/nav.html`
- [ ] `templates/components/pagination.html`
- [ ] `templates/components/table.html`
- [ ] `templates/components/form_field.html`

---

### 6.2 Dashboard

**Priority:** LOW
**Dependencies:** All major features
**Complexity:** MEDIUM

**Web Interface:**
- [ ] Homepage dashboard with statistics
- [ ] Quick actions (add student, create exam, etc.)
- [ ] Recent activity feed
- [ ] Alerts (missing grades, overdue submissions)
- [ ] Statistics:
  - Total students, courses, exams
  - Grading progress
  - Recent enrollments
- [ ] Charts (grade distribution, enrollment trends)

**Libraries:**
- [ ] Chart.js for visualizations

---

### 6.3 Search & Filtering

**Priority:** MEDIUM
**Dependencies:** All list pages
**Complexity:** MEDIUM

**Tasks:**
- [ ] Global search (students, courses, exams)
- [ ] Advanced filters on list pages
- [ ] Saved filter presets
- [ ] Export filtered results

**Implementation:**
- [ ] Full-text search (SQLite FTS5 or simple LIKE)
- [ ] Query builder for complex filters
- [ ] URL parameter encoding for shareable filters

---

## Future Enhancements (Phase 7+)

### User Authentication & Authorization
- [ ] User registration and login
- [ ] Role-based access control (admin, lecturer, assistant)
- [ ] Permission system for courses
- [ ] Password reset functionality

### Notifications
- [ ] Email notifications (submission received, grades published)
- [ ] In-app notifications
- [ ] Configurable notification preferences

### Advanced Grading
- [ ] Rubric-based grading
- [ ] Peer review system
- [ ] Grade curves and normalization
- [ ] Late submission penalties

### Reporting & Analytics
- [ ] Custom report builder
- [ ] Export to PDF
- [ ] Performance analytics (student, course level)
- [ ] Comparative statistics

### API
- [ ] RESTful API for all operations
- [ ] API authentication (tokens)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Webhooks for integrations

### Integration
- [ ] LMS integration (Moodle, Canvas)
- [ ] Calendar integration (iCal export)
- [ ] Cloud storage (Dropbox, Google Drive)
- [ ] Plagiarism detection services

---

## Implementation Priority Summary

### Must Have (MVP)
1. University Management
2. Student Management
3. Course Management
4. Student Enrollment
5. Exam Creation
6. Submission Tracking
7. Grading System
8. File Storage System
9. Audit Log System

### Should Have
10. Multi-Part Exams
11. Grade Monitoring
12. Email Parser
13. Document Parser
14. Student Import
15. Grade Export
16. Grade Change Tracking
17. UI Components

### Nice to Have
18. Student Export
19. Manual Document Assignment
20. Dashboard
21. Search & Filtering
22. Advanced features (authentication, notifications, etc.)

---

## Estimated Timeline

- **Phase 1** (Core Data Management): 2-3 weeks
- **Phase 2** (Examination System): 2-3 weeks
- **Phase 3** (Document Management): 2-3 weeks
- **Phase 4** (Import/Export): 1 week
- **Phase 5** (Audit & Logging): 1 week
- **Phase 6** (UI Polish): 1-2 weeks

**Total MVP:** 9-13 weeks
