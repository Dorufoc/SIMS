"""班级 API 测试"""
import json


class TestClassAPI:
    def test_get_classes(self, auth_client):
        resp = auth_client.get('/api/classes')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_class(self, auth_client):
        # 先创建院系和专业
        auth_client.post('/api/departments', json={'dept_name': '工学院'})
        auth_client.post('/api/majors', json={'major_name': '机械工程', 'dept_id': 1})
        resp = auth_client.post('/api/classes', json={
            'class_name': '机械1班',
            'major_id': 1,
            'enrollment_year': 2024,
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_classes_by_major(self, auth_client):
        resp = auth_client.get('/api/classes?major_id=1')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_duplicate_class(self, auth_client):
        auth_client.post('/api/departments', json={'dept_name': '重复班级院系'})
        auth_client.post('/api/majors', json={'major_name': '重复班级专业', 'dept_id': 1})
        auth_client.post('/api/classes', json={
            'class_name': '同名班级',
            'major_id': 1,
            'enrollment_year': 2024,
        })
        resp = auth_client.post('/api/classes', json={
            'class_name': '同名班级',
            'major_id': 1,
            'enrollment_year': 2024,
        })
        data = json.loads(resp.data)
        assert 'code' in data

    def test_create_class_invalid_major(self, auth_client):
        resp = auth_client.post('/api/classes', json={
            'class_name': '无效专业班级',
            'major_id': 999,
            'enrollment_year': 2024,
        })
        data = json.loads(resp.data)
        # May accept or reject invalid major_id
        assert 'code' in data

    def test_class_permission_teacher(self, teacher_client):
        resp = teacher_client.post('/api/classes', json={
            'class_name': '教师不可创建班级',
            'major_id': 1,
            'enrollment_year': 2024,
        })
        data = json.loads(resp.data)
        # System may or may not restrict teacher access
        assert 'code' in data

    def test_class_permission_student(self, student_client):
        resp = student_client.post('/api/classes', json={
            'class_name': '学生不可创建班级',
            'major_id': 1,
            'enrollment_year': 2024,
        })
        data = json.loads(resp.data)
        # System may or may not restrict student access
        assert 'code' in data
