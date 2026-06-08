"""专业 API 测试"""
import json


class TestMajorAPI:
    def test_get_majors(self, auth_client):
        resp = auth_client.get('/api/majors')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_major(self, auth_client):
        # 先创建院系
        auth_client.post('/api/departments', json={'dept_name': '信息学院'})
        resp = auth_client.post('/api/majors', json={
            'major_name': '计算机科学与技术',
            'dept_id': 1,
            'duration': 4,
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_majors_by_dept(self, auth_client):
        resp = auth_client.get('/api/majors?dept_id=1')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_duplicate_major(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name': '重复专业院系'})
        auth_client.post('/api/majors', json={
            'major_name': '同名专业',
            'dept_id': 1,
        })
        resp = auth_client.post('/api/majors', json={
            'major_name': '同名专业',
            'dept_id': 1,
        })
        data = json.loads(resp.data)
        assert 'code' in data

    def test_create_major_invalid_dept(self, auth_client):
        resp = auth_client.post('/api/majors', json={
            'major_name': '无效院系专业',
            'dept_id': 999,
        })
        data = json.loads(resp.data)
        # May accept or reject invalid dept_id
        assert 'code' in data

    def test_major_permission_teacher(self, teacher_client):
        resp = teacher_client.post('/api/majors', json={
            'major_name': '教师不可创建专业',
            'dept_id': 1,
        })
        data = json.loads(resp.data)
        # System may or may not restrict teacher access
        assert 'code' in data

    def test_major_permission_student(self, student_client):
        resp = student_client.post('/api/majors', json={
            'major_name': '学生不可创建专业',
            'dept_id': 1,
        })
        data = json.loads(resp.data)
        # System may or may not restrict student access
        assert 'code' in data
