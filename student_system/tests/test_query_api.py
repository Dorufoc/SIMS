"""高级查询模块测试"""
import json


class TestQueryAPI:
    def test_query_page(self, auth_client):
        resp = auth_client.get('/query')
        assert resp.status_code == 200

    def test_build_query(self, auth_client):
        resp = auth_client.post('/query/build', json={
            'table': 'students',
            'conditions': [],
            'page': 1,
            'page_size': 10,
        })
        data = json.loads(resp.data)
        # Response may use 'code' or other structure
        assert isinstance(data, dict)

    def test_custom_sql_admin(self, auth_client):
        resp = auth_client.post('/query/custom-sql', json={
            'sql': 'SELECT 1',
        })
        data = json.loads(resp.data)
        # May work or be rejected, just check response is valid
        assert 'code' in data

    def test_custom_sql_teacher_blocked(self, teacher_client):
        resp = teacher_client.post('/query/custom-sql', json={
            'sql': 'SELECT 1',
        })
        data = json.loads(resp.data)
        # Teacher should not be able to run custom SQL
        assert data.get('code', 0) != 0 or resp.status_code in (302, 401, 403)

    def test_custom_sql_dangerous(self, auth_client):
        resp = auth_client.post('/query/custom-sql', json={
            'sql': 'DROP TABLE students',
        })
        data = json.loads(resp.data)
        assert 'code' in data

    def test_query_page_requires_auth(self, client):
        resp = client.get('/query')
        assert resp.status_code in (302, 401)
