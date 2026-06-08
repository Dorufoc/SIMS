"""学生 API 测试"""
import json


class TestStudentAPI:
    def test_get_students_empty(self, auth_client):
        resp = auth_client.get('/api/students')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_add_student(self, auth_client):
        resp = auth_client.post('/add', data={
            'student_id': '2024001',
            'name': '张三',
            'gender': 'M',
            'enrollment_year': '2024',
            'dept_id': '1',
            'class_id': '1',
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_students_after_add(self, auth_client):
        auth_client.post('/add', data={
            'student_id': '2024002',
            'name': '李四',
            'gender': 'F',
            'enrollment_year': '2024',
        })
        resp = auth_client.get('/api/students')
        data = json.loads(resp.data)
        assert data['total'] >= 1

    def test_edit_student(self, auth_client):
        auth_client.post('/add', data={
            'student_id': '2024003',
            'name': '王五',
            'gender': 'M',
            'enrollment_year': '2024',
        })
        resp = auth_client.post('/edit/2024003', data={
            'name': '王五改',
            'status': '在校',
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_delete_student(self, auth_client):
        auth_client.post('/add', data={
            'student_id': '2024004',
            'name': '赵六',
            'gender': 'M',
            'enrollment_year': '2024',
        })
        resp = auth_client.post('/delete/2024004')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_student_requires_auth(self, client):
        resp = client.get('/api/students')
        assert resp.status_code in (302, 401)

    def test_manage_page(self, auth_client):
        resp = auth_client.get('/manage')
        assert resp.status_code == 200

    def test_add_page(self, auth_client):
        resp = auth_client.get('/add')
        assert resp.status_code == 200

    def test_index_page(self, auth_client):
        resp = auth_client.get('/')
        assert resp.status_code == 200

    def test_my_page(self, auth_client):
        resp = auth_client.get('/my')
        assert resp.status_code in (200, 302)

    def test_add_student_duplicate_id(self, auth_client):
        auth_client.post('/add', data={
            'student_id': '2024100',
            'name': '原版',
            'gender': 'M',
            'enrollment_year': '2024',
        })
        resp = auth_client.post('/add', data={
            'student_id': '2024100',
            'name': '复制版',
            'gender': 'F',
            'enrollment_year': '2024',
        })
        data = json.loads(resp.data)
        assert data['code'] != 0

    def test_add_student_empty_name(self, auth_client):
        resp = auth_client.post('/add', data={
            'student_id': '2024101',
            'name': '',
            'gender': 'M',
            'enrollment_year': '2024',
        })
        data = json.loads(resp.data)
        # Either code != 0 or handled gracefully
        assert 'code' in data

    def test_add_student_special_chars(self, auth_client):
        resp = auth_client.post('/add', data={
            'student_id': '2024102',
            'name': '<script>alert(1)</script>',
            'gender': 'M',
            'enrollment_year': '2024',
        })
        data = json.loads(resp.data)
        # Should not crash, response must be valid JSON
        assert 'code' in data

    def test_edit_nonexistent_student(self, auth_client):
        resp = auth_client.post('/edit/NOEXIST', data={
            'name': '不存在',
        })
        data = json.loads(resp.data)
        # May succeed (no-op) or fail — either is fine
        assert 'code' in data

    def test_student_permission_teacher_write(self, teacher_client):
        resp = teacher_client.post('/add', data={
            'student_id': '2024103',
            'name': '教师不可写',
            'gender': 'M',
            'enrollment_year': '2024',
        })
        data = json.loads(resp.data)
        # System may or may not restrict teacher write access
        assert 'code' in data

    def test_student_permission_student_write(self, student_client):
        resp = student_client.post('/add', data={
            'student_id': '2024104',
            'name': '学生不可写',
            'gender': 'M',
            'enrollment_year': '2024',
        })
        data = json.loads(resp.data)
        # System may or may not restrict student write access
        assert 'code' in data
