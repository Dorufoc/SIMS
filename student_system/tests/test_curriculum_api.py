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

    def test_get_list_by_major_and_year(self, populated_db):
        c = populated_db
        c.post('/api/courses', json={"course_id":"CUR002","course_name":"查询课","credits":3,"hours":48,"type":"必修"})
        c.post('/api/curriculum', json={"course_id":"CUR002","major_id":1,"enrollment_year":2024,"recommended_term":1})
        resp = c.get('/api/curriculum?major_id=1&enrollment_year=2024')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_student_curriculum(self, populated_db_full):
        c = populated_db_full
        c.post('/api/courses', json={"course_id":"CUR003","course_name":"培养课","credits":2,"hours":32,"type":"必修"})
        c.post('/api/curriculum', json={"course_id":"CUR003","major_id":1,"enrollment_year":2024,"recommended_term":1})
        resp = c.get('/api/students/2024001/curriculum')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_update(self, populated_db):
        c = populated_db
        c.post('/api/courses', json={"course_id":"CUR004","course_name":"更新课","credits":2,"hours":32,"type":"必修"})
        c.post('/api/curriculum', json={"course_id":"CUR004","major_id":1,"enrollment_year":2024,"recommended_term":1})
        resp = c.put('/api/curriculum/1', json={"recommended_term":2})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_delete(self, populated_db):
        c = populated_db
        c.post('/api/courses', json={"course_id":"CUR005","course_name":"待删课","credits":2,"hours":32,"type":"必修"})
        c.post('/api/curriculum', json={"course_id":"CUR005","major_id":1,"enrollment_year":2024,"recommended_term":1})
        resp = c.delete('/api/curriculum/1')
        data = json.loads(resp.data)
        assert data["code"] == 0
