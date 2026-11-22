"""
Student Management System
-------------------------
Stack : Python Flask + SQLite + HTML + CSS + JavaScript
Run   : python app.py   ->  http://127.0.0.1:5000

Database (students.db) is created automatically on first run and filled with
sample students, so nothing has to be set up by hand.
"""
import csv
import io
import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, Response, g, jsonify, render_template, request

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get("SMS_DB_PATH", os.path.join(BASE_DIR, "students.db"))

COURSES = [
    "B.Tech CSE", "B.Tech IT", "B.Tech ECE", "B.Tech Mechanical",
    "B.Tech Civil", "BCA", "MCA", "MBA", "B.Sc",
]
STATUSES = ["Active", "Inactive"]
GENDERS = ["Male", "Female", "Other"]
SORTABLE = {
    "name": "name", "roll_no": "roll_no", "course": "course", "year": "year",
    "cgpa": "cgpa", "status": "status", "created_at": "created_at",
}

app = Flask(__name__)
app.json.sort_keys = False


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no     TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    phone       TEXT NOT NULL,
    gender      TEXT NOT NULL,
    dob         TEXT,
    course      TEXT NOT NULL,
    year        INTEGER NOT NULL,
    cgpa        REAL NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'Active',
    address     TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

SEED = [
    ("CS2023001", "Aarav Sharma", "aarav.sharma@example.com", "9876543210", "Male", "2004-03-14", "B.Tech CSE", 3, 8.9, "Active", "12, Vijay Nagar, Indore"),
    ("CS2023002", "Ananya Verma", "ananya.verma@example.com", "9876501234", "Female", "2004-07-22", "B.Tech CSE", 3, 9.2, "Active", "45, Palasia, Indore"),
    ("IT2024003", "Rohan Patel", "rohan.patel@example.com", "9822011223", "Male", "2005-01-09", "B.Tech IT", 2, 7.8, "Active", "8, Rau Circle, Indore"),
    ("EC2022004", "Kavya Joshi", "kavya.joshi@example.com", "9755012345", "Female", "2003-11-30", "B.Tech ECE", 4, 8.4, "Active", "21, Sudama Nagar, Indore"),
    ("ME2024005", "Vikram Singh", "vikram.singh@example.com", "9993012345", "Male", "2005-05-18", "B.Tech Mechanical", 2, 6.9, "Active", "77, Bhawarkua, Indore"),
    ("CV2023006", "Priya Chouhan", "priya.chouhan@example.com", "9827098765", "Female", "2004-09-02", "B.Tech Civil", 3, 7.5, "Inactive", "3, Annapurna Road, Indore"),
    ("CA2025007", "Mohit Yadav", "mohit.yadav@example.com", "9425011122", "Male", "2006-02-25", "BCA", 1, 7.2, "Active", "19, Mhow Naka, Indore"),
    ("MC2024008", "Sneha Agrawal", "sneha.agrawal@example.com", "9179033445", "Female", "2001-12-05", "MCA", 2, 8.7, "Active", "56, Saket Nagar, Indore"),
    ("MB2024009", "Arjun Mishra", "arjun.mishra@example.com", "9111022334", "Male", "2000-08-11", "MBA", 2, 8.1, "Active", "9, Scheme 54, Indore"),
    ("CS2025010", "Ishita Gupta", "ishita.gupta@example.com", "9685077889", "Female", "2006-06-27", "B.Tech CSE", 1, 9.0, "Active", "34, Geeta Bhawan, Indore"),
    ("SC2023011", "Nikhil Rathore", "nikhil.rathore@example.com", "9926055667", "Male", "2004-04-04", "B.Sc", 3, 6.5, "Inactive", "63, Bengali Square, Indore"),
    ("IT2022012", "Tanvi Deshmukh", "tanvi.deshmukh@example.com", "9039044556", "Female", "2003-10-16", "B.Tech IT", 4, 8.8, "Active", "27, Nipania, Indore"),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the table and insert sample data when the table is empty."""
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        now = datetime.now()
        for i, row in enumerate(SEED):
            stamp = now.replace(microsecond=0).isoformat(sep=" ")
            # stagger the created time so "recent admissions" looks natural
            created = datetime.fromtimestamp(now.timestamp() - (len(SEED) - i) * 3600).replace(microsecond=0).isoformat(sep=" ")
            db.execute(
                """INSERT INTO students
                   (roll_no, name, email, phone, gender, dob, course, year, cgpa,
                    status, address, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*row, created, stamp),
            )
        db.commit()
    db.close()


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_payload(data):
    """Validate + normalise incoming JSON. Returns (clean_dict, errors_dict)."""
    data = data or {}
    errors = {}
    out = {}

    def text(key):
        return str(data.get(key, "") if data.get(key) is not None else "").strip()

    out["roll_no"] = text("roll_no").upper()
    if not out["roll_no"]:
        errors["roll_no"] = "Roll number is required."
    elif not re.match(r"^[A-Z0-9\-_/]{3,20}$", out["roll_no"]):
        errors["roll_no"] = "Use 3-20 letters, numbers, - or _."

    out["name"] = re.sub(r"\s+", " ", text("name"))
    if len(out["name"]) < 2:
        errors["name"] = "Enter the student's full name."
    elif len(out["name"]) > 80:
        errors["name"] = "Name is too long (max 80 characters)."

    out["email"] = text("email").lower()
    if not EMAIL_RE.match(out["email"]):
        errors["email"] = "Enter a valid email address."

    phone_raw = text("phone")
    digits = re.sub(r"[\s\-+()]", "", phone_raw)
    if not digits.isdigit() or not (10 <= len(digits) <= 13):
        errors["phone"] = "Enter a valid phone number (10 digits)."
    out["phone"] = phone_raw

    out["gender"] = text("gender")
    if out["gender"] not in GENDERS:
        errors["gender"] = "Select a gender."

    out["dob"] = text("dob")
    if out["dob"]:
        try:
            d = datetime.strptime(out["dob"], "%Y-%m-%d")
            if d > datetime.now():
                errors["dob"] = "Date of birth cannot be in the future."
        except ValueError:
            errors["dob"] = "Use a valid date."

    out["course"] = text("course")
    if out["course"] not in COURSES:
        errors["course"] = "Select a course."

    try:
        out["year"] = int(data.get("year"))
        if not 1 <= out["year"] <= 4:
            raise ValueError
    except (TypeError, ValueError):
        errors["year"] = "Year must be between 1 and 4."

    try:
        out["cgpa"] = round(float(data.get("cgpa")), 2)
        if not 0 <= out["cgpa"] <= 10:
            raise ValueError
    except (TypeError, ValueError):
        errors["cgpa"] = "CGPA must be a number from 0 to 10."

    out["status"] = text("status") or "Active"
    if out["status"] not in STATUSES:
        errors["status"] = "Select a status."

    out["address"] = text("address")
    if len(out["address"]) > 250:
        errors["address"] = "Address is too long (max 250 characters)."

    return out, errors


def error_response(errors, code=400):
    return jsonify({"ok": False, "message": "Please fix the highlighted fields.", "errors": errors}), code


def integrity_errors(exc):
    msg = str(exc).lower()
    errors = {}
    if "roll_no" in msg:
        errors["roll_no"] = "This roll number already exists."
    if "email" in msg:
        errors["email"] = "This email is already registered."
    return errors or {"roll_no": "Duplicate record."}


def find_duplicates(db, clean, exclude_id=None):
    """SQLite only reports one violated constraint, so check both fields up front."""
    errors = {}
    skip = exclude_id if exclude_id is not None else -1
    if db.execute("SELECT 1 FROM students WHERE roll_no = ? AND id != ?", (clean["roll_no"], skip)).fetchone():
        errors["roll_no"] = "This roll number already exists."
    if db.execute("SELECT 1 FROM students WHERE email = ? AND id != ?", (clean["email"], skip)).fetchone():
        errors["email"] = "This email is already registered."
    return errors


def row_to_dict(row):
    return {k: row[k] for k in row.keys()}


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", courses=COURSES, statuses=STATUSES, genders=GENDERS)


# --------------------------------------------------------------------------
# REST API
# --------------------------------------------------------------------------
@app.get("/api/students")
def list_students():
    q = request.args.get("q", "").strip()
    course = request.args.get("course", "").strip()
    status = request.args.get("status", "").strip()
    sort = SORTABLE.get(request.args.get("sort", "created_at"), "created_at")
    order = "ASC" if request.args.get("order", "desc").lower() == "asc" else "DESC"
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(50, max(1, int(request.args.get("per_page", 8))))
    except ValueError:
        page, per_page = 1, 8

    where, params = [], []
    if q:
        like = f"%{q}%"
        where.append("(name LIKE ? OR roll_no LIKE ? OR email LIKE ? OR phone LIKE ?)")
        params += [like, like, like, like]
    if course:
        where.append("course = ?")
        params.append(course)
    if status:
        where.append("status = ?")
        params.append(status)
    clause = ("WHERE " + " AND ".join(where)) if where else ""

    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM students {clause}", params).fetchone()[0]
    pages = max(1, -(-total // per_page))
    page = min(page, pages)
    # `sort` / `order` come from a whitelist above, so this f-string is safe
    rows = db.execute(
        f"SELECT * FROM students {clause} ORDER BY {sort} {order}, id DESC LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page],
    ).fetchall()
    return jsonify({
        "items": [row_to_dict(r) for r in rows],
        "total": total, "page": page, "pages": pages, "per_page": per_page,
    })


@app.get("/api/students/<int:sid>")
def get_student(sid):
    row = get_db().execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    if not row:
        return jsonify({"ok": False, "message": "Student not found."}), 404
    return jsonify(row_to_dict(row))


@app.post("/api/students")
def create_student():
    clean, errors = clean_payload(request.get_json(silent=True))
    if errors:
        return error_response(errors)
    now = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    db = get_db()
    dupes = find_duplicates(db, clean)
    if dupes:
        return error_response(dupes, 409)
    try:
        cur = db.execute(
            """INSERT INTO students
               (roll_no, name, email, phone, gender, dob, course, year, cgpa,
                status, address, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (clean["roll_no"], clean["name"], clean["email"], clean["phone"],
             clean["gender"], clean["dob"], clean["course"], clean["year"],
             clean["cgpa"], clean["status"], clean["address"], now, now),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        return error_response(integrity_errors(exc), 409)
    row = db.execute("SELECT * FROM students WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify({"ok": True, "message": "Student added successfully.", "student": row_to_dict(row)}), 201


@app.put("/api/students/<int:sid>")
def update_student(sid):
    db = get_db()
    if not db.execute("SELECT 1 FROM students WHERE id = ?", (sid,)).fetchone():
        return jsonify({"ok": False, "message": "Student not found."}), 404
    clean, errors = clean_payload(request.get_json(silent=True))
    if errors:
        return error_response(errors)
    now = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    dupes = find_duplicates(db, clean, exclude_id=sid)
    if dupes:
        return error_response(dupes, 409)
    try:
        db.execute(
            """UPDATE students SET roll_no=?, name=?, email=?, phone=?, gender=?,
               dob=?, course=?, year=?, cgpa=?, status=?, address=?, updated_at=?
               WHERE id=?""",
            (clean["roll_no"], clean["name"], clean["email"], clean["phone"],
             clean["gender"], clean["dob"], clean["course"], clean["year"],
             clean["cgpa"], clean["status"], clean["address"], now, sid),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        return error_response(integrity_errors(exc), 409)
    row = db.execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    return jsonify({"ok": True, "message": "Student record updated.", "student": row_to_dict(row)})


@app.delete("/api/students/<int:sid>")
def delete_student(sid):
    db = get_db()
    cur = db.execute("DELETE FROM students WHERE id = ?", (sid,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"ok": False, "message": "Student not found."}), 404
    return jsonify({"ok": True, "message": "Student deleted."})


@app.get("/api/stats")
def stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    active = db.execute("SELECT COUNT(*) FROM students WHERE status='Active'").fetchone()[0]
    avg = db.execute("SELECT AVG(cgpa) FROM students").fetchone()[0] or 0
    top = db.execute("SELECT name, cgpa FROM students ORDER BY cgpa DESC LIMIT 1").fetchone()
    by_course = db.execute(
        "SELECT course, COUNT(*) AS count FROM students GROUP BY course ORDER BY count DESC, course"
    ).fetchall()
    by_year = db.execute(
        "SELECT year, COUNT(*) AS count FROM students GROUP BY year ORDER BY year"
    ).fetchall()
    recent = db.execute("SELECT * FROM students ORDER BY created_at DESC, id DESC LIMIT 5").fetchall()
    return jsonify({
        "total": total, "active": active, "inactive": total - active,
        "avg_cgpa": round(avg, 2),
        "topper": row_to_dict(top) if top else None,
        "by_course": [row_to_dict(r) for r in by_course],
        "by_year": [row_to_dict(r) for r in by_year],
        "recent": [row_to_dict(r) for r in recent],
    })


@app.get("/api/export.csv")
def export_csv():
    rows = get_db().execute("SELECT * FROM students ORDER BY roll_no").fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Roll No", "Name", "Email", "Phone", "Gender", "DOB", "Course",
                     "Year", "CGPA", "Status", "Address", "Added On"])
    for r in rows:
        writer.writerow([r["roll_no"], r["name"], r["email"], r["phone"], r["gender"],
                         r["dob"], r["course"], r["year"], r["cgpa"], r["status"],
                         r["address"], r["created_at"]])
    return Response(
        "\ufeff" + buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"},
    )


@app.errorhandler(404)
def not_found(_e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "message": "Not found."}), 404
    return render_template("index.html", courses=COURSES, statuses=STATUSES, genders=GENDERS), 404


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  Student Management System running at  http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
