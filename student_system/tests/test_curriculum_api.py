"""培养计划 API 测试"""
import json


def _ensure_course(client, suffix=''):
    """创建院系→专业→课程，返回 client。"""
    client.post('/api/departments', json={
        'dept_name': f'课程学院{suffix}', 'dean': '张教授', 'phone': '010-11111111'})
    client.post('/api/majors', json={
        'major_name': f'课程专业{suffix}', 'dept_id': 1, 'duration': 4})
    client.post('/api/courses', json={
        'course_id': f'CS{suffix}', 'course_name': f'测试课程{suffix}',
        'credits': 4, 'hours': 64, 'type': '必修'})
    return client


class TestCurriculumAPI:
    def test_get_curriculum(self, auth_client):
        resp = auth_client.get('/api/curriculum')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_curriculum(self, auth_client):
        cl = _ensure_course(auth_client, '101')
        resp = cl.post('/api/curriculum', json={
            'major_id': 1,
            'enrollment_year': 2024,
            'course_id': 'CS101',
            'course_type': '必修',
            'recommended_term': '第一学期',
            'is_core': True,
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_curriculum_after_create(self, auth_client):
        cl = _ensure_course(auth_client, '102')
        cl.post('/api/curriculum', json={
            'major_id': 1,
            'enrollment_year': 2024,
            'course_id': 'CS102',
            'course_type': '必修',
            'recommended_term': '第一学期',
            'is_core': True,
        })
        resp = cl.get('/api/curriculum')
        data = json.loads(resp.data)
        assert data['code'] == 0
        assert data['total'] >= 1

    def test_curriculum_permission_teacher(self, teacher_client):
        resp = teacher_client.post('/api/curriculum', json={
            'major_id': 1,
            'enrollment_year': 2024,
            'course_id': 'CS101',
        })
        data = json.loads(resp.data)
        assert 'code' in data

    def test_delete_curriculum(self, auth_client):
        cl = _ensure_course(auth_client, '103')
        cl.post('/api/curriculum', json={
            'major_id': 1,
            'enrollment_year': 2024,
            'course_id': 'CS103',
            'course_type': '必修',
            'recommended_term': '第一学期',
            'is_core': True,
        })
        resp = cl.delete('/api/curriculum/1')
        data = json.loads(resp.data)
        assert data['code'] == 0
