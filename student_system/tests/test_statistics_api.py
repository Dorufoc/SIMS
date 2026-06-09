# -*- coding: utf-8 -*-
"""API 集成测试 — 统计"""
import json

class TestStatisticsAPI:
    def test_dashboard(self, auth_client):
        resp = auth_client.get('/api/statistics/dashboard')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_students_by_dept(self, auth_client):
        resp = auth_client.get('/api/statistics/students')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_gender_distribution(self, auth_client):
        resp = auth_client.get('/api/statistics/gender')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_grade_distribution(self, auth_client):
        resp = auth_client.get('/api/statistics/grades')
        data = json.loads(resp.data)
        assert data["code"] == 0
