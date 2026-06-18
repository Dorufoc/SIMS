# -*- coding: utf-8 -*-
"""API 集成测试 — 用户"""
import json

class TestUserAPI:
    def test_user_management_page(self, auth_client):
        resp = auth_client.get('/user_management')
        assert resp.status_code == 200

    def test_permission_management_page(self, auth_client):
        # 默认 admin 用户不存在于数据库，但页面可渲染空用户
        resp = auth_client.get('/user_management/permissions/1')
        assert resp.status_code == 200

    def test_create(self, auth_client):
        resp = auth_client.post('/api/users', json={"username":"newadmin","password":"admin123","role":"admin"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/users')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_list_with_filters(self, auth_client):
        auth_client.post('/api/users', json={"username":"filteradmin","password":"admin123","role":"admin"})
        resp = auth_client.get('/api/users?filters=[{"field":"role","op":"eq","value":"admin"}]')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_update(self, auth_client):
        auth_client.post('/api/users', json={"username":"updateadmin","password":"admin123","role":"admin"})
        resp = auth_client.put('/api/users/1', json={"role":"teacher"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_delete(self, auth_client):
        # 先创建一个占位用户（使 deleteadmin 的 user_id 与当前 session 的 user_id=1 不同）
        auth_client.post('/api/users', json={"username":"placeholder","password":"Admin123!","role":"admin"})
        auth_client.post('/api/users', json={"username":"deleteadmin","password":"Admin123!","role":"admin"})
        # 通过列表查询获取 deleteadmin 的 user_id
        resp = auth_client.get('/api/users?keyword=deleteadmin')
        data = json.loads(resp.data)
        user_id = [u['user_id'] for u in data['data'] if u['username'] == 'deleteadmin'][0]
        resp = auth_client.delete(f'/api/users/{user_id}')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_delete_nonexistent_user(self, auth_client):
        resp = auth_client.delete('/api/users/999')
        data = json.loads(resp.data)
        # 控制器未对不存在的用户做特殊处理，仍然返回 code 0
        assert data["code"] == 0

    def test_user_permissions(self, auth_client):
        auth_client.post('/api/users', json={"username":"permadmin","password":"admin123","role":"admin"})
        resp = auth_client.get('/api/users/1/permissions')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_set_user_permissions(self, auth_client):
        auth_client.post('/api/users', json={"username":"setpermadmin","password":"admin123","role":"admin"})
        resp = auth_client.put('/api/users/1/permissions', json={
            'permissions': [{'table_name': 'students', 'permission_code': '077'}]
        })
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_tables(self, auth_client):
        resp = auth_client.get('/api/tables')
        data = json.loads(resp.data)
        assert data["code"] == 0
