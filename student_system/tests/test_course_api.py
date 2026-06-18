# -*- coding: utf-8 -*-
"""API 集成测试 — 课程"""
import json

class TestCourseAPI:
    def test_courses_page(self, auth_client):
        resp = auth_client.get('/courses')
        assert resp.status_code == 200

    def test_create(self, auth_client):
        resp = auth_client.post('/api/courses', json={'course_id':'CS999','course_name':'测试课','credits':4,'hours':64,'type':'必修'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/courses')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list_with_filters(self, auth_client):
        auth_client.post('/api/courses', json={'course_id':'CS998','course_name':'过滤课','credits':3,'hours':48,'type':'选修','dept_name':'计算机学院'})
        resp = auth_client.get('/api/courses?filters=[{"field":"type","op":"eq","value":"选修"}]')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_detail(self, auth_client):
        auth_client.post('/api/courses', json={'course_id':'CS997','course_name':'详情课','credits':2,'hours':32,'type':'必修'})
        resp = auth_client.get('/api/courses/CS997')
        data = json.loads(resp.data)
        assert data['code'] == 0
        assert data['data']['course_name'] == '详情课'

    def test_update(self, auth_client):
        auth_client.post('/api/courses', json={'course_id':'CS996','course_name':'原课','credits':2,'hours':32,'type':'必修'})
        resp = auth_client.put('/api/courses/CS996', json={'course_name':'更新课'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_delete(self, auth_client):
        auth_client.post('/api/courses', json={'course_id':'CS995','course_name':'待删','credits':1,'hours':16,'type':'必修'})
        resp = auth_client.delete('/api/courses/CS995')
        data = json.loads(resp.data)
        assert data['code'] == 0
