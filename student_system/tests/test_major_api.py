# -*- coding: utf-8 -*-
"""API 集成测试 — 专业"""
import json


class TestMajorAPI:
    def test_majors_page(self, auth_client):
        resp = auth_client.get('/majors')
        assert resp.status_code == 200

    def test_create(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name': '计院'})
        resp = auth_client.post('/api/majors', json={'major_name': '测试专业', 'dept_id': 1, 'duration': 4})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/majors')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_major_detail(self, populated_db):
        resp = populated_db.get('/api/majors/1')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_update_major(self, populated_db):
        resp = populated_db.put('/api/majors/1', json={'major_name': '新专业名'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_delete_major(self, auth_client):
        # 新建一个没有关联班级的专业再删除
        auth_client.post('/api/departments', json={'dept_name': '文学院'})
        auth_client.post('/api/majors', json={'major_name': '中文', 'dept_id': 1, 'duration': 4})
        resp = auth_client.delete('/api/majors/1')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_api_delete_major_with_classes(self, auth_client):
        """删除存在关联班级的专业应失败"""
        auth_client.post('/api/departments', json={'dept_name': '理学院'})
        auth_client.post('/api/majors', json={'major_name': '物理', 'dept_id': 2, 'duration': 4})
        auth_client.post('/api/classes', json={'class_name': '物理1班', 'major_id': 2, 'enrollment_year': 2024})
        resp = auth_client.delete('/api/majors/2')
        data = json.loads(resp.data)
        assert data['code'] == 1

    def test_api_delete_nonexistent_major(self, auth_client):
        resp = auth_client.delete('/api/majors/9999')
        data = json.loads(resp.data)
        assert data['code'] == 1
