# -*- coding: utf-8 -*-
"""API 集成测试 — 院系"""
import json


class TestDepartmentAPI:
    def test_departments_page(self, auth_client):
        resp = auth_client.get('/departments')
        assert resp.status_code == 200

    def test_create(self, auth_client):
        resp = auth_client.post('/api/departments', json={'dept_name': '测试学院', 'dean': '院长', 'phone': '010-1234'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/departments')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_update(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name': '原学院'})
        resp = auth_client.put('/api/departments/1', json={'dept_name': '新学院', 'dean': '新院长'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_delete(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name': '待删学院'})
        resp = auth_client.delete('/api/departments/1')
        data = json.loads(resp.data)
        assert data['code'] == 0
