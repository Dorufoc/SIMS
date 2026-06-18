# -*- coding: utf-8 -*-
"""API 集成测试 — 选课"""
import json

class TestEnrollmentAPI:
    def test_enrollments_page(self, auth_client):
        resp = auth_client.get('/enrollments')
        assert resp.status_code == 200

    def test_grades_page(self, auth_client):
        resp = auth_client.get('/grades')
        assert resp.status_code == 200

    def test_enroll(self, populated_db_full):
        c = populated_db_full
        resp = c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_available_courses(self, populated_db_full):
        resp = populated_db_full.get('/api/enrollment/available?student_id=2024001')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_drop(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        resp = c.post('/api/enrollment/1/drop')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_api_grades(self, populated_db_full):
        c = populated_db_full
        resp = c.get('/api/grades')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_api_enrollments(self, populated_db_full):
        c = populated_db_full
        resp = c.get('/api/enrollments')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_student_enrolled_courses(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        resp = c.get('/api/students/2024001/enrolled-courses')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_grade_add(self, populated_db_full):
        c = populated_db_full
        resp = c.post('/api/grades/add', json={"student_id":"2024001","course_id":"CS101","score":85})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_grade_template(self, auth_client):
        resp = auth_client.get('/api/import/grade/template')
        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'

    def test_grade_import(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        resp = c.post('/api/grades/import', json={
            "data": [["2024001", "CS101", "88"]]
        })
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_grade_export(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        resp = c.get('/api/import/grade/export')
        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'

    def test_student_enrollment(self, populated_db_full):
        resp = populated_db_full.get('/api/students/2024001/enrollment')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_student_enrollments_alias(self, populated_db_full):
        resp = populated_db_full.get('/api/students/2024001/enrollments')
        data = json.loads(resp.data)
        assert data["code"] == 0
