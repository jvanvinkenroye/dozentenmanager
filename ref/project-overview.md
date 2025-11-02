# Dozentenmanager - Project Overview

## Purpose

Dozentenmanager is a comprehensive student management system designed to help lecturers and academic staff manage students, courses, exams, and grading processes across multiple universities.

## Core Functionality

### Student Management
- Manage student information:
  - First and last names
  - Student ID numbers (Matrikelnummer)
  - Email addresses
  - Study programs
- Students belong to universities
- Students can enroll in one or more courses
- Ability to register and unregister students from courses
- Import and export student data

### Course Management
- Organize courses by:
  - University (Hochschule)
  - Semester
  - Course name (Lehrveranstaltung)
- Track student attendance and participation

### Examination & Grading System
- Exams can consist of one or multiple components
- Track submission status (submitted/not submitted)
- Assign points to exam submissions
- Convert points to grades
- Monitor whether grades have been entered
- Record grade changes with audit trail

### Document Management
- Automatic file organization structure:
  ```
  Hochschule/Semester/Lehrveranstaltung/NachnameVorname/
  Example: th-koeln/2023_SoSe/EinfuehrungStatistik/MuellerMike/
  ```

### Document Processing
- **Email Parser**:
  - Check for attachments in emails
  - Automatic assignment of attachments to students
  - Manual assignment fallback for unmatched attachments

- **Document Parser** (PDF & Word):
  - Extract content from submitted documents
  - Automatic student assignment
  - Manual assignment fallback

### Audit & Logging
- All changes are logged for accountability
- Grade modification history
- Track who made changes and when

## Target Users

- University lecturers
- Teaching assistants
- Academic administrators
- Course coordinators

## Key Benefits

1. Centralized student data management
2. Automated document processing and filing
3. Transparent grading workflow
4. Complete audit trail for academic integrity
5. Multi-university support
6. Flexible exam structure (single or multi-part)

## Project Status

This project is in the initial planning phase. The concept has been defined, and implementation will follow a structured approach:
1. Build individual features as CLI tools
2. Add linting and code quality checks
3. Integrate features into Flask web application
4. Deploy as web service

## Related Documentation

- [Architecture](./architecture.md) - Technical implementation details
- [Data Model](./data-model.md) - Database schema and relationships
- [Features](./features.md) - Detailed feature breakdown
- [Development Workflow](./development-workflow.md) - Development process and guidelines
