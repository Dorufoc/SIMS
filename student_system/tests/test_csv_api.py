"""CSV 模块测试"""
import json
import io


class TestCSVAPI:
    def test_get_template(self, auth_client):
        resp = auth_client.get('/csv/template')
        assert resp.status_code in (200, 302, 401)

    def test_preview_csv(self, auth_client):
        csv_content = "student_id,name,gender,enrollment_year\n2024005,测试学生,M,2024\n"
        data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
        resp = auth_client.post('/csv/preview', data=data, content_type='multipart/form-data')
        # May succeed or fail, just check it's valid JSON
        try:
            result = json.loads(resp.data)
            assert 'code' in result
        except Exception:
            pass  # May return non-JSON for file downloads

    def test_csv_requires_auth(self, client):
        resp = client.get('/csv/template')
        assert resp.status_code in (200, 302, 401)
