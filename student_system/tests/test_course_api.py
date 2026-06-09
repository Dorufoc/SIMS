# -*- coding: utf-8 -*-
"""API 集成测试 — 课程"""
import json

class TestCourseAPI:
    def test_create(self, auth_client):
        resp = auth_client.post('/api/courses', json={'course_id':'CS999','course_name':'测试课','credits':4,'hours':64,'type':'必修'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/courses')
        data = json.loads(resp.data)
        assert data['code'] == 0
