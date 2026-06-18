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

    def test_register_success(self, client, reset_tables):
        # 注册依赖学生表中存在对应的学号，且密码需满足强度策略
        from entity.base import SessionLocal
        from entity.student import Student
        db = SessionLocal()
        db.add(Student(student_id='S99001', name='测试学生', gender='M', enrollment_year=2024,
                       status='在校'))
        db.commit()
        db.close()
        resp = client.post('/register', data={
            'password': 'Test123!',
            'real_name': '测试',
            'role': 'student',
            'register_method': 'ref_id',
            'register_value': 'S99001'
        })
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

    def test_set_username_page(self, auth_client):
        resp = auth_client.get('/set-username')
        assert resp.status_code == 200

    def test_api_set_username(self, auth_client):
        auth_client.post('/api/users', json={
            'username': 'nameadmin', 'password': 'OldPass1!', 'role': 'admin'
        })
        with auth_client.session_transaction() as sess:
            sess.clear()
        resp = auth_client.post('/login', data={'username': 'nameadmin', 'password': 'OldPass1!'})
        assert json.loads(resp.data)['code'] == 0
        resp = auth_client.post('/api/set-username', json={'username': 'newadminname'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_set_username_invalid(self, client):
        resp = client.post('/api/set-username', json={'username': 'newname'})
        data = json.loads(resp.data)
        assert data['code'] == 1

    def test_user_me_authenticated(self, auth_client):
        resp = auth_client.get('/api/user/me')
        data = json.loads(resp.data)
        assert data['code'] == 0
        assert data['data']['role'] == 'admin'

    def test_user_me_unauthenticated(self, client):
        resp = client.get('/api/user/me')
        assert resp.status_code == 401

    def test_change_password_success(self, auth_client):
        # 先创建一个已知密码的管理员账号，再修改密码
        auth_client.post('/api/users', json={
            'username': 'pwdadmin', 'password': 'OldPass1!', 'role': 'admin'
        })
        # 使用同一 session 不够，需要登录为新用户
        with auth_client.session_transaction() as sess:
            sess.clear()
        resp = auth_client.post('/login', data={'username': 'pwdadmin', 'password': 'OldPass1!'})
        data = json.loads(resp.data)
        assert data['code'] == 0
        resp = auth_client.post('/api/change-password', json={
            'old_password': 'OldPass1!', 'new_password': 'NewPass2!'
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_change_password_wrong_old(self, auth_client):
        # 使用 auth_client 默认 session 中 user_id 在数据库可能不存在，返回错误即可覆盖分支
        resp = auth_client.post('/api/change-password', json={
            'old_password': 'wrong', 'new_password': 'NewPass2!'
        })
        data = json.loads(resp.data)
        assert data['code'] == 1
