# EduDesk – Student Management System
**Internship Task 2 (Easy) – Full Stack Development**

A full-stack web application to manage student records.
**Tech stack:** Python Flask · SQLite · HTML · CSS · JavaScript (responsive UI)

## Task requirements covered
| Task workflow step | Where it is implemented |
|---|---|
| Step 1 – Design the frontend interface | `templates/index.html`, `static/css/style.css`, `static/js/app.js` |
| Step 2 – Create backend APIs | REST API in `app.py` (`/api/students`, `/api/stats`, `/api/export.csv`) |
| Step 3 – Implement database connectivity | SQLite (`students.db`, auto-created + sample data) |
| Step 4 – Add CRUD operations | Add, View, Update, Delete students |
| Step 5 – Test application functionality | `tests/test_api.py` (automated tests) |

**Key features:** Add Students · Update Records · Delete Records · View Student Details

**Extras:** dashboard with charts, live search, course/status filter, sorting, pagination,
server + browser validation (duplicate roll no / email blocked), CSV export, mobile responsive layout.

## How to run (2 minutes)
Requirement: **Python 3.9+** (https://www.python.org/downloads/)

### Windows
Double-click **`run.bat`**  (it installs Flask and opens the browser automatically).

### Linux / macOS
```bash
./run.sh
```

### Manual way (any OS)
```bash
pip install -r requirements.txt
python app.py
```
Then open **http://127.0.0.1:5000**

> The database file is created automatically on first run with 12 sample students.
> To start fresh, stop the server and delete `students.db`.

## REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/students?q=&course=&status=&sort=&order=&page=&per_page=` | List / search / filter / paginate |
| GET | `/api/students/<id>` | View one student |
| POST | `/api/students` | Add student |
| PUT | `/api/students/<id>` | Update student |
| DELETE | `/api/students/<id>` | Delete student |
| GET | `/api/stats` | Dashboard numbers |
| GET | `/api/export.csv` | Download all records as CSV |

## Run the automated tests
```bash
python -m unittest discover -s tests -v
```

## Project structure
```
student_management_system/
├── app.py              # Flask app, REST API, SQLite, validation
├── requirements.txt
├── run.bat / run.sh    # one-click launchers
├── templates/index.html
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── img/favicon.svg
└── tests/test_api.py
```

## Screenshots to submit
Take screenshots of: Dashboard, Students list, Add form, Edit form, Details popup, Delete confirmation.
