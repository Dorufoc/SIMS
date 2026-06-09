# -*- coding: utf-8 -*-
"""API 集成测试 — 培养计划"""
import json

class TestCurriculumAPI:
    def test_create(self, populated_db):
        c = populated_db
        # 课程表需要提前存在的 course
        c.post('/api/courses', json={"course_id":"CUR001","course_name":"测试课","credits":4,"hours":64,"type":"必修"})
        resp = c.post('/api/curriculum', json={"course_id":"CUR001","major_id":1,"enrollment_year":2024,"recommended_term":1})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/curriculum')
        data = json.loads(resp.data)
        assert data["code"] == 0
