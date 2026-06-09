# -*- coding: utf-8 -*-
"""API 集成测试 — E2E 流程"""
import json

class TestTeachingFlow:
    def test_full_flow(self, auth_client):
        c = auth_client
        r1 = c.post('/api/departments', json={'dept_name':'E2E学院','dean':'王院长'})
        assert json.loads(r1.data)['code'] == 0
        r2 = c.post('/api/majors', json={'major_name':'E2E专业','dept_id':1,'duration':4})
        assert json.loads(r2.data)['code'] == 0
        r3 = c.post('/api/classes', json={'class_name':'E2E班','major_id':1,'enrollment_year':2024})
        assert json.loads(r3.data)['code'] == 0
        r4 = c.post('/api/teachers', json={'teacher_id':'E2ET01','name':'E2E教师'})
        assert json.loads(r4.data)['code'] == 0
        r5 = c.post('/api/courses', json={'course_id':'E2EC01','course_name':'E2E课程','credits':3})
        assert json.loads(r5.data)['code'] == 0
        r6 = c.post('/api/semesters', json={'academic_year':'2025-2026','semester_name':'E2E学期','start_date':'2025-09-01','end_date':'2026-01-15'})
        assert json.loads(r6.data)['code'] == 0
