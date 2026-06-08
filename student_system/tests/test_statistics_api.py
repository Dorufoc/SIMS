"""统计 API 测试"""
import json


class TestStatisticsAPI:
    def test_dashboard_stats(self, auth_client):
        resp = auth_client.get('/api/statistics/dashboard')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_gender_stats(self, auth_client):
        resp = auth_client.get('/api/statistics/gender')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_grades_stats(self, auth_client):
        resp = auth_client.get('/api/statistics/grades')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_gpa_stats(self, auth_client):
        resp = auth_client.get('/api/statistics/gpa_ranking')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_student_status_stats(self, auth_client):
        resp = auth_client.get('/api/statistics/student_status')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_students_stats(self, auth_client):
        resp = auth_client.get('/api/statistics/students')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_statistics_page(self, auth_client):
        resp = auth_client.get('/statistics')
        assert resp.status_code == 200

    def test_stats_requires_auth(self, client):
        resp = client.get('/api/statistics/dashboard')
        assert resp.status_code in (302, 401)
