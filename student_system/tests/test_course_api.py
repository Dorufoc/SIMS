"""课程 API 测试"""
import json


class TestCourseAPI:
    def test_get_courses_empty(self, auth_client):
        resp = auth_client.get('/api/courses')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_course(self, auth_client):
        resp = auth_client.post('/api/courses', json={
            'course_id': 'CS101',
            'course_name': '数据结构',
            'credits': 4,
            'hours': 64,
            'type': '必修',
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_courses_after_create(self, populated_db):
        resp = populated_db.get('/api/courses')
        data = json.loads(resp.data)
        assert data['code'] == 0
        course_ids = [c['course_id'] for c in data['data']]
        assert 'CS101' in course_ids

    def test_create_course_missing_fields(self, auth_client):
        resp = auth_client.post('/api/courses', json={
            'course_name': '无编号课程',
        })
        data = json.loads(resp.data)
        assert data['code'] != 0

    def test_create_duplicate_course(self, auth_client):
        auth_client.post('/api/courses', json={
            'course_id': 'CS200',
            'course_name': '操作系统',
            'credits': 4,
        })
        resp = auth_client.post('/api/courses', json={
            'course_id': 'CS200',
            'course_name': '操作系统重复',
            'credits': 4,
        })
        data = json.loads(resp.data)
        assert data['code'] != 0

    def test_update_course(self, auth_client):
        auth_client.post('/api/courses', json={
            'course_id': 'CS300',
            'course_name': '编译原理',
            'credits': 3,
        })
        resp = auth_client.put('/api/courses/CS300', json={
            'course_name': '编译原理（修订）',
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_update_nonexistent_course(self, auth_client):
        resp = auth_client.put('/api/courses/NOEXIST', json={
            'course_name': '不存在的课程',
        })
        data = json.loads(resp.data)
        assert data['code'] != 0

    def test_delete_course(self, auth_client):
        auth_client.post('/api/courses', json={
            'course_id': 'CS400',
            'course_name': '待删课程',
            'credits': 2,
        })
        resp = auth_client.delete('/api/courses/CS400')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_delete_nonexistent_course(self, auth_client):
        resp = auth_client.delete('/api/courses/NOEXIST')
        data = json.loads(resp.data)
        assert 'code' in data

    def test_course_permission_teacher(self, teacher_client):
        resp = teacher_client.post('/api/courses', json={
            'course_id': 'CS999',
            'course_name': '教师尝试创建',
        })
        data = json.loads(resp.data)
        assert resp.status_code == 403 or data.get('code', 0) != 0

    def test_course_permission_student(self, student_client):
        resp = student_client.post('/api/courses', json={
            'course_id': 'CS998',
            'course_name': '学生尝试创建',
        })
        data = json.loads(resp.data)
        assert resp.status_code == 403 or data.get('code', 0) != 0

    def test_courses_page(self, auth_client):
        resp = auth_client.get('/courses')
        assert resp.status_code == 200
