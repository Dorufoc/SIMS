# -*- coding: utf-8 -*-
"""API 集成测试 — 班级"""
import json


class TestClassAPI:
    def test_classes_page(self, auth_client):
        resp = auth_client.get('/classes')
        assert resp.status_code == 200

    def test_create(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name': '计院'})
        auth_client.post('/api/majors', json={'major_name': 'CS', 'dept_id': 1, 'duration': 4})
        resp = auth_client.post('/api/classes', json={'class_name': '测试班', 'major_id': 1, 'enrollment_year': 2024})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/classes')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_class_detail(self, populated_db):
        resp = populated_db.get('/api/classes/1')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_update_class(self, populated_db):
        resp = populated_db.put('/api/classes/1', json={'class_name': '新班名'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_delete_class(self, populated_db):
        resp = populated_db.delete('/api/classes/1')
        data = json.loads(resp.data)
        assert data['code'] == 0
