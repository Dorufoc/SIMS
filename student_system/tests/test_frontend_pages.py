# -*- coding: utf-8 -*-
"""API 集成测试 — 前端页面可访问性"""
import json

class TestPublicPages:
    def test_login_page(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_register_page(self, client):
        resp = client.get('/register')
        assert resp.status_code == 200

class TestProtectedPagesUnauthenticated:
    def test_index_redirects(self, client):
        resp = client.get('/')
        assert resp.status_code in (302, 401)

class TestProtectedPagesAuthenticated:
    def test_index(self, auth_client):
        resp = auth_client.get('/')
        assert resp.status_code == 200

    def test_manage(self, auth_client):
        resp = auth_client.get('/manage')
        assert resp.status_code == 200

    def test_add_student(self, auth_client):
        resp = auth_client.get('/add')
        assert resp.status_code == 200

    def test_statistics(self, auth_client):
        resp = auth_client.get('/statistics')
        assert resp.status_code == 200

    def test_query(self, auth_client):
        resp = auth_client.get('/query')
        assert resp.status_code == 200
