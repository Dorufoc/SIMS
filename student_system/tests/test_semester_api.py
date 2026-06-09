# -*- coding: utf-8 -*-
"""API 集成测试 — 学期"""
import json

class TestSemesterAPI:
    def test_create(self, auth_client):
        resp = auth_client.post('/api/semesters', json={"academic_year":"2025-2026","semester_name":"第一学期","start_date":"2025-09-01","end_date":"2026-01-15"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/semesters')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_set_current(self, auth_client):
        auth_client.post('/api/semesters', json={"academic_year":"2025-2026","semester_name":"第一学期","start_date":"2025-09-01","end_date":"2026-01-15"})
        resp = auth_client.post('/api/semesters/1/set_current')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_current_by_list(self, auth_client):
        """通过查询列表获取当前学期（无单独/current路由）"""
        auth_client.post('/api/semesters', json={"academic_year":"2025-2026","semester_name":"第一学期","start_date":"2025-09-01","end_date":"2026-01-15"})
        resp = auth_client.get('/api/semesters')
        data = json.loads(resp.data)
        assert data["code"] == 0
