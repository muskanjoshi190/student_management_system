"""Automated tests for the REST API.  Run:  python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["SMS_DB_PATH"] = _tmp.name

import app as sms  # noqa: E402

VALID = {
    "roll_no": "TS2025001", "name": "Test Student", "email": "test.student@example.com",
    "phone": "9876543210", "gender": "Female", "dob": "2005-05-05", "course": "BCA",
    "year": 2, "cgpa": 8.25, "status": "Active", "address": "Indore",
}


class StudentAPITests(unittest.TestCase):
    def setUp(self):
        self.client = sms.app.test_client()

    def test_01_seeded_and_list(self):
        r = self.client.get("/api/students?per_page=50")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.json["total"], 12)

    def test_02_create_read_update_delete(self):
        r = self.client.post("/api/students", json=VALID)
        self.assertEqual(r.status_code, 201)
        sid = r.json["student"]["id"]

        self.assertEqual(self.client.get(f"/api/students/{sid}").json["name"], "Test Student")

        upd = dict(VALID, name="Renamed Student", cgpa=9.1)
        r = self.client.put(f"/api/students/{sid}", json=upd)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["student"]["cgpa"], 9.1)

        self.assertEqual(self.client.delete(f"/api/students/{sid}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/students/{sid}").status_code, 404)

    def test_03_validation(self):
        bad = dict(VALID, email="nope", cgpa=15, year=9, phone="12")
        r = self.client.post("/api/students", json=bad)
        self.assertEqual(r.status_code, 400)
        for k in ("email", "cgpa", "year", "phone"):
            self.assertIn(k, r.json["errors"])

    def test_04_duplicates(self):
        data = dict(VALID, roll_no="DUP2025", email="dup@example.com")
        self.assertEqual(self.client.post("/api/students", json=data).status_code, 201)
        r = self.client.post("/api/students", json=data)
        self.assertEqual(r.status_code, 409)
        self.assertIn("roll_no", r.json["errors"])
        self.assertIn("email", r.json["errors"])

    def test_05_search_filter_sort_paginate(self):
        r = self.client.get("/api/students?q=aarav")
        self.assertEqual(r.json["total"], 1)
        r = self.client.get("/api/students?course=MBA")
        self.assertTrue(all(s["course"] == "MBA" for s in r.json["items"]))
        r = self.client.get("/api/students?sort=cgpa&order=desc&per_page=3")
        cg = [s["cgpa"] for s in r.json["items"]]
        self.assertEqual(cg, sorted(cg, reverse=True))
        self.assertEqual(len(cg), 3)
        # SQL injection attempt in sort/search must not break anything
        r = self.client.get("/api/students?sort=name;DROP TABLE students&q=' OR 1=1 --")
        self.assertEqual(r.status_code, 200)

    def test_06_stats_and_export(self):
        r = self.client.get("/api/stats")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["total"], r.json["active"] + r.json["inactive"])
        r = self.client.get("/api/export.csv")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Roll No", r.get_data(as_text=True))

    def test_07_pages(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.delete("/api/students/99999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
