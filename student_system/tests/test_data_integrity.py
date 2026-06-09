# -*- coding: utf-8 -*-
"""API 集成测试 — 数据完整性"""
import json

class TestUniqueConstraints:
    def test_duplicate_student_id(self, auth_client):
        auth_client.post('/add', data={'student_id':'DUP001','name':'第一个','enrollment_year':'2024'})
        resp = auth_client.post('/add', data={'student_id':'DUP001','name':'第二个','enrollment_year':'2024'})
        data = json.loads(resp.data)
        assert data['code'] != 0

    def test_duplicate_teacher_id(self, auth_client):
        auth_client.post('/api/teachers', json={'teacher_id':'TEADUP','name':'教师一'})
        resp = auth_client.post('/api/teachers', json={'teacher_id':'TEADUP','name':'教师二'})
        data = json.loads(resp.data)
        assert data['code'] != 0

    def test_student_count_consistency(self, auth_client):
        auth_client.post('/add', data={'student_id':'CNT001','name':'计数测试','enrollment_year':'2024'})
        resp = auth_client.get('/api/students')
        data = json.loads(resp.data)
        assert data['code'] == 0
        assert data['total'] >= 1
