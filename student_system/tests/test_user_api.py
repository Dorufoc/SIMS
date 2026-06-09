# -*- coding: utf-8 -*-
"""API 集成测试 — 用户"""
import json

class TestUserAPI:
    def test_create(self, auth_client):
        resp = auth_client.post('/api/users', json={"username":"newadmin","password":"admin123","role":"admin"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/users')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_tables(self, auth_client):
        resp = auth_client.get('/api/tables')
        data = json.loads(resp.data)
        assert data["code"] == 0
