# -*- coding: utf-8 -*-
"""API 集成测试 — 认证"""
import json

class TestAuthAPI:
    def test_login_page(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_register_page(self, client):
        resp = client.get('/register')
        assert resp.status_code == 200

    def test_register_success(self, client):
        resp = client.post('/register', data={'password':'123456','real_name':'测试','role':'student','register_method':'ref_id','register_value':'S99001'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_login_invalid(self, client):
        resp = client.post('/login', data={'username':'nonexistent','password':'wrong'})
        data = json.loads(resp.data)
        assert data['code'] == 1

    def test_logout(self, auth_client):
        resp = auth_client.get('/logout')
        assert resp.status_code == 302

    def test_change_password_unauthenticated(self, client):
        resp = client.post('/api/change-password', json={'old_password':'old','new_password':'new'})
        data = json.loads(resp.data)
        assert data['code'] == 1

    def test_login_empty_fields(self, client):
        resp = client.post('/login', data={'username':'','password':''})
        data = json.loads(resp.data)
        assert data['code'] != 0

    def test_csrf_token(self, client):
        resp = client.get('/api/csrf-token')
        data = json.loads(resp.data)
        assert data['code'] == 0
        assert 'token' in data

    def test_user_me_authenticated(self, auth_client):
        resp = auth_client.get('/api/user/me')
        data = json.loads(resp.data)
        assert data['code'] == 0
        assert data['data']['role'] == 'admin'

    def test_user_me_unauthenticated(self, client):
        resp = client.get('/api/user/me')
        assert resp.status_code == 401
