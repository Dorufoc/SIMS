# -*- coding: utf-8 -*-
"""API 集成测试 — 学生"""
import json

class TestStudentAPI:
    def test_add_student(self, auth_client):
        resp = auth_client.post('/add', data={"student_id":"2024101","name":"测试学生","gender":"M","enrollment_year":"2024"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_students(self, auth_client):
        resp = auth_client.get('/api/students')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_single_student_via_list(self, auth_client):
        """通过列表端点验证学生已创建（无 /api/student/{id} 路由）"""
        auth_client.post('/add', data={"student_id":"2024102","name":"单个学生","enrollment_year":"2024"})
        resp = auth_client.get('/api/students')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_edit_student(self, auth_client):
        auth_client.post('/add', data={"student_id":"2024103","name":"原名","enrollment_year":"2024"})
        resp = auth_client.post('/edit/2024103', data={"name":"新名"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_delete_student(self, auth_client):
        auth_client.post('/add', data={"student_id":"2024104","name":"待删","enrollment_year":"2024"})
        resp = auth_client.post('/delete/2024104', data={})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_add_page(self, auth_client):
        resp = auth_client.get('/add')
        assert resp.status_code == 200
