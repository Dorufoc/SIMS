# -*- coding: utf-8 -*-
"""API 集成测试 — 授课"""
import json


class TestTeachingAPI:
    def test_teaching_page(self, auth_client):
        resp = auth_client.get('/teaching')
        assert resp.status_code == 200

    def test_create(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name': '计院'})
        auth_client.post('/api/majors', json={'major_name': 'CS', 'dept_id': 1, 'duration': 4})
        auth_client.post('/api/teachers', json={'teacher_id': 'TT001', 'name': '李教授'})
        auth_client.post('/api/courses', json={'course_id': 'TT101', 'course_name': '数据结构', 'credits': 4})
        auth_client.post('/api/semesters', json={'academic_year': '2025-2026', 'semester_name': '第一学期', 'start_date': '2025-09-01', 'end_date': '2026-01-15'})
        resp = auth_client.post('/api/teaching', json={'course_id': 'TT101', 'teacher_id': 'TT001', 'semester_id': 1, 'classroom': 'A101', 'schedule': '周一1-2节', 'capacity': 60})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/teaching')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_teacher_teaching(self, populated_db_full):
        resp = populated_db_full.get('/api/teachers/T001/teaching')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_get_teaching(self, populated_db_full):
        resp = populated_db_full.get('/api/teaching/1')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_update_teaching(self, populated_db_full):
        resp = populated_db_full.put('/api/teaching/1', json={'classroom': 'B202'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_delete_teaching(self, populated_db_full):
        resp = populated_db_full.delete('/api/teaching/1')
        data = json.loads(resp.data)
        assert data['code'] == 0
