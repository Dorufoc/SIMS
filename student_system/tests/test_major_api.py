# -*- coding: utf-8 -*-
"""API 集成测试 — 专业"""
import json

class TestMajorAPI:
    def test_create(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name':'计院'})
        resp = auth_client.post('/api/majors', json={'major_name':'测试专业','dept_id':1,'duration':4})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/majors')
        data = json.loads(resp.data)
        assert data['code'] == 0
