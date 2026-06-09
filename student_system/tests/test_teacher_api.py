# -*- coding: utf-8 -*-
"""API 集成测试 — 教师"""
import json

class TestTeacherAPI:
    def test_create(self, auth_client):
        resp = auth_client.post('/api/teachers', json={'teacher_id':'T999','name':'测试教师','gender':'M','title':'教授'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/teachers')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_update(self, auth_client):
        auth_client.post('/api/teachers', json={'teacher_id':'T998','name':'原名'})
        resp = auth_client.put('/api/teachers/T998', json={'name':'新名','title':'副教授'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_delete(self, auth_client):
        auth_client.post('/api/teachers', json={'teacher_id':'T997','name':'待删'})
        resp = auth_client.delete('/api/teachers/T997')
        data = json.loads(resp.data)
        assert data['code'] == 0
