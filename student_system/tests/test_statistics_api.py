# -*- coding: utf-8 -*-
"""API 集成测试 — 统计"""
import json

class TestStatisticsAPI:
    def test_statistics_page(self, auth_client):
        resp = auth_client.get('/statistics')
        assert resp.status_code == 200

    def test_dashboard(self, auth_client):
        resp = auth_client.get('/api/statistics/dashboard')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_students_by_dept(self, auth_client):
        resp = auth_client.get('/api/statistics/students')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_gender_distribution(self, auth_client):
        resp = auth_client.get('/api/statistics/gender')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_student_status(self, auth_client):
        resp = auth_client.get('/api/statistics/student_status')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_grade_distribution(self, auth_client):
        resp = auth_client.get('/api/statistics/grades')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_grade_distribution_with_teaching(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        c.put('/api/enrollment/1/score', json={'score': 90})
        resp = c.get('/api/statistics/grades?teaching_id=1')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_class_grade_stats(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        c.put('/api/enrollment/1/score', json={'score': 90})
        resp = c.get('/api/statistics/class_grades')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_class_grade_stats_with_semester(self, populated_db_full):
        c = populated_db_full
        resp = c.get('/api/statistics/class_grades?semester_id=1')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_gpa_ranking(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        c.put('/api/enrollment/1/score', json={'score': 90})
        resp = c.get('/api/statistics/gpa_ranking?limit=10')
        data = json.loads(resp.data)
        assert data["code"] == 0
