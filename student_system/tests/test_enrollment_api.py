# -*- coding: utf-8 -*-
"""API 集成测试 — 选课"""
import json

class TestEnrollmentAPI:
    def test_enroll(self, populated_db_full):
        c = populated_db_full
        resp = c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_available_courses(self, populated_db_full):
        resp = populated_db_full.get('/api/enrollment/available?student_id=2024001')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_student_enrollment(self, populated_db_full):
        resp = populated_db_full.get('/api/students/2024001/enrollment')
        data = json.loads(resp.data)
        assert data["code"] == 0
