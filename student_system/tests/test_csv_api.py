# -*- coding: utf-8 -*-
"""API 集成测试 — CSV"""
import json

class TestCSVAPI:
    def test_csv_template(self, auth_client):
        resp = auth_client.get('/csv/template')
        assert resp.status_code in (200, 302)

    def test_csv_export(self, auth_client):
        resp = auth_client.get('/csv/export')
        assert resp.status_code in (200, 302)

    def test_csv_preview(self, auth_client):
        from io import BytesIO
        resp = auth_client.post('/csv/preview', data={
            'file': (BytesIO(b'\xe5\xad\xa6\xe5\x8f\xb7,\xe5\xa7\x93\xe5\x90\x8d,\xe6\x80\xa7\xe5\x88\xab,\xe5\x85\xa5\xe5\xad\xa6\xe5\xb9\xb4\xe4\xbb\xbd\nS88801,\xe9\xa2\x84\xe8\xa7\x88\xe7\x94\x9f,\xe7\x94\xb7,2024'), 'students.csv')
        })
        data = json.loads(resp.data)
        assert "valid_data" in data or "errors" in data

    def test_csv_import(self, auth_client):
        resp = auth_client.post('/csv/import', json={
            'data': [{'student_id': 'S88802', 'name': '导入生', 'gender': 'M', 'enrollment_year': 2024}]
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_batch_template(self, auth_client):
        resp = auth_client.get('/api/import/student/template')
        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'

    def test_batch_template_unsupported(self, auth_client):
        resp = auth_client.get('/api/import/unknown/template')
        assert resp.status_code == 400

    def test_batch_import(self, auth_client):
        resp = auth_client.post('/api/import/student/import', json={
            'data': [{'student_id': 'S88803', 'name': '批量导入生', 'gender': 'M', 'enrollment_year': 2024}]
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_batch_export(self, auth_client):
        resp = auth_client.get('/api/import/student/export')
        assert resp.status_code == 200
        assert resp.mimetype == 'text/csv'
