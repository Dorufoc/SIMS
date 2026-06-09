# -*- coding: utf-8 -*-
"""API 集成测试 — 奖惩"""
import json

class TestRewardAPI:
    def test_create(self, auth_client):
        auth_client.post('/add', data={'student_id':'R999','name':'奖惩生','enrollment_year':'2024'})
        resp = auth_client.post('/api/rewards_punishments', json={'student_id':'R999','rp_type':'奖励','title':'优秀','level':'校级','date':'2025-01-01','reason':'成绩优异','issuing_authority':'学生处'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/rewards_punishments')
        data = json.loads(resp.data)
        assert data['code'] == 0
