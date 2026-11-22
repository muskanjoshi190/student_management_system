# EduDesk – Student Management System

A modern, responsive web application designed to simplify student record management. EduDesk provides an intuitive dashboard and an organized interface for managing student information efficiently.

## Overview

EduDesk is a full-stack web application built with Python Flask and SQLite. It allows users to manage student records through a clean interface with essential data management features, search functionality, and reporting capabilities.

## Technology Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **UI:** Responsive web design
- **API:** RESTful APIs

## Key Features

- **Dashboard:** View student statistics and record summaries.
- **Add Students:** Register new students with validated information.
- **View Details:** Access individual student profiles and information.
- **Update Records:** Edit existing student details.
- **Delete Records:** Remove student entries with confirmation.
- **Live Search:** Find students using search functionality.
- **Filtering:** Filter records by course and status.
- **Sorting:** Organize student records using sorting options.
- **Pagination:** Navigate through student records efficiently.
- **CSV Export:** Download student records in CSV format.
- **Form Validation:** Prevent duplicate roll numbers and email addresses.
- **Responsive Design:** Access the application across desktop, tablet, and mobile devices.

## Application Workflow

1. The frontend provides an interactive interface for managing student records.
2. Flask handles application requests and backend operations.
3. REST APIs connect the frontend with the backend.
4. SQLite stores student information persistently.
5. CRUD operations allow users to create, view, update, and delete records.
6. Automated tests help verify API functionality.

## Getting Started

### Prerequisites

- Python 3.9 or later
- pip (Python package manager)

### Installation

1. Download or clone the project repository.
2. Open the project directory in a terminal.
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Run the Application

**Windows**

Double-click `run.bat` to install dependencies and launch the application.

**Linux / macOS**

```bash
./run.sh
```

**Manual Execution**

```bash
python app.py
```

Once the server starts, open the application at:

```text
http://127.0.0.1:5000
```

### Database Initialization

The SQLite database is automatically created when the application runs for the first time. It is initialized with 12 sample student records for demonstration.

To reset the application data, stop the server and delete the `students.db` file. The database will be recreated on the next launch.

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/students` | Retrieve, search, filter, sort, and paginate student records |
| GET | `/api/students/<id>` | Retrieve an individual student |
| POST | `/api/students` | Add a new student |
| PUT | `/api/students/<id>` | Update student information |
| DELETE | `/api/students/<id>` | Delete a student record |
| GET | `/api/stats` | Retrieve dashboard statistics |
| GET | `/api/export.csv` | Export student records as a CSV file |

### Supported Query Parameters

The student listing endpoint supports:

- `q` – Search students
- `course` – Filter by course
- `status` – Filter by student status
- `sort` – Select sorting field
- `order` – Set sorting order
- `page` – Select page number
- `per_page` – Set records per page

## Automated Testing

The project includes automated API tests to verify application functionality.

Run the test suite using:

```bash
python -m unittest discover -s tests -v
```

## Project Structure

```text
student_management_system/
│
├── app.py
├── requirements.txt
├── run.bat
├── run.sh
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── img/
│       └── favicon.svg
│
└── tests/
    └── test_api.py
```

## Future Enhancements

- User authentication and role-based access.
- Advanced student performance reports.
- Additional filtering and reporting options.
- Improved data visualization.
- Database migration and backup functionality.

## Project Purpose

EduDesk aims to make student information management simpler, more organized, and efficient through a responsive interface and a structured backend system.
