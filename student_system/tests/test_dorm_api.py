# -*- coding: utf-8 -*-
"""API 集成测试 — 宿舍"""
import json


class TestDormAPI:
    def test_dorm_rooms_page(self, auth_client):
        resp = auth_client.get('/dorm_rooms')
        assert resp.status_code == 200

    def test_dorm_assignments_page(self, auth_client):
        resp = auth_client.get('/dorm_assignments')
        assert resp.status_code == 200

    def test_create_room(self, auth_client):
        resp = auth_client.post('/api/dorm_rooms', json={"building": "1号楼", "room_number": "101", "capacity": 4})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_rooms(self, auth_client):
        resp = auth_client.get('/api/dorm_rooms')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_api_dorm_room_detail(self, auth_client):
        auth_client.post('/api/dorm_rooms', json={"building": "1号楼", "room_number": "103", "capacity": 4})
        resp = auth_client.get('/api/dorm_rooms/1')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_api_update_dorm_room(self, auth_client):
        auth_client.post('/api/dorm_rooms', json={"building": "1号楼", "room_number": "104", "capacity": 4})
        resp = auth_client.put('/api/dorm_rooms/1', json={"capacity": 6})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_api_delete_dorm_room(self, auth_client):
        auth_client.post('/api/dorm_rooms', json={"building": "1号楼", "room_number": "105", "capacity": 4})
        resp = auth_client.delete('/api/dorm_rooms/1')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_buildings(self, auth_client):
        resp = auth_client.get('/api/dorm_buildings')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_available_rooms(self, auth_client):
        resp = auth_client.get('/api/dorm_rooms/available')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_api_dorm_assignments(self, auth_client):
        resp = auth_client.get('/api/dorm_assignments')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_assign(self, auth_client):
        auth_client.post('/add', data={"student_id": "D001", "name": "住宿生", "enrollment_year": "2024"})
        auth_client.post('/api/dorm_rooms', json={"building": "1号楼", "room_number": "102", "capacity": 4})
        resp = auth_client.post('/api/dorm_assignments', json={"student_id": "D001", "room_id": 1, "bed_number": "1"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_api_checkout(self, auth_client):
        auth_client.post('/add', data={"student_id": "D002", "name": "退宿生", "enrollment_year": "2024"})
        auth_client.post('/api/dorm_rooms', json={"building": "1号楼", "room_number": "106", "capacity": 4})
        auth_client.post('/api/dorm_assignments', json={"student_id": "D002", "room_id": 1, "bed_number": "1"})
        resp = auth_client.post('/api/dorm_assignments/1/checkout', json={})
        data = json.loads(resp.data)
        assert data["code"] == 0
