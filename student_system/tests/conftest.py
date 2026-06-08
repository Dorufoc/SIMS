"""测试配置"""
import os
import sys
import pytest
import secrets

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用 SQLite 内存数据库进行测试
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key'

from main import app, init_db


def _setup_session(sess):
    """设置会话中的 CSRF token"""
    if '_csrf_token' not in sess:
        sess['_csrf_token'] = secrets.token_hex(32)


@pytest.fixture
def client():
    """Flask 测试客户端"""
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


@pytest.fixture
def auth_client(client):
    """已登录的测试客户端（admin）"""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'admin'
        sess['user_role'] = 'admin'
        sess['user_ref_id'] = 'admin001'
        sess['user_uuid'] = '00000000-0000-0000-0000-000000000001'
        sess['username_changed'] = True
        _setup_session(sess)
    return client


@pytest.fixture
def teacher_client(client):
    """已登录的测试客户端（teacher 角色）"""
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_name'] = 'teacher_test'
        sess['user_role'] = 'teacher'
        sess['user_ref_id'] = 'T001'
        sess['user_uuid'] = '00000000-0000-0000-0000-000000000002'
        sess['username_changed'] = True
        _setup_session(sess)
    return client


@pytest.fixture
def student_client(client):
    """已登录的测试客户端（student 角色）"""
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['user_name'] = 'student_test'
        sess['user_role'] = 'student'
        sess['user_ref_id'] = 'S2024001'
        sess['user_uuid'] = '00000000-0000-0000-0000-000000000003'
        sess['username_changed'] = True
        _setup_session(sess)
    return client


@pytest.fixture
def populated_db(auth_client):
    """预填充基础数据：1个院系 + 1个专业 + 1个班级 + 1个学生 + 1个教师"""
    client = auth_client
    # 创建院系
    client.post('/api/departments', json={'dept_name': '计算机学院', 'dean': '张教授', 'phone': '010-12345678'})
    # 创建专业
    client.post('/api/majors', json={'major_name': '计算机科学与技术', 'dept_id': 1, 'duration': 4})
    # 创建班级
    client.post('/api/classes', json={'class_name': '计科1班', 'major_id': 1, 'enrollment_year': 2024})
    # 创建教师
    client.post('/api/teachers', json={'teacher_id': 'T001', 'name': '李教授', 'gender': 'M', 'title': '教授'})
    # 创建课程
    client.post('/api/courses', json={'course_id': 'CS101', 'course_name': '数据结构', 'credits': 4, 'hours': 64, 'type': '必修'})
    # 创建学期
    client.post('/api/semesters', json={'academic_year': '2024-2025', 'semester_name': '第一学期', 'start_date': '2024-09-01', 'end_date': '2025-01-15'})
    return client


@pytest.fixture
def populated_db_full(auth_client):
    """预填充完整数据：院系/专业/班级/学生/教师/课程/学期/授课"""
    client = auth_client
    # 创建院系
    client.post('/api/departments', json={'dept_name': '计算机学院', 'dean': '张教授', 'phone': '010-12345678'})
    # 创建专业
    client.post('/api/majors', json={'major_name': '计算机科学与技术', 'dept_id': 1, 'duration': 4})
    # 创建班级
    client.post('/api/classes', json={'class_name': '计科1班', 'major_id': 1, 'enrollment_year': 2024})
    # 创建学生
    client.post('/add', data={
        'student_id': '2024001',
        'name': '张三',
        'gender': 'M',
        'enrollment_year': '2024',
        'dept_id': '1',
        'class_id': '1',
    })
    # 创建教师
    client.post('/api/teachers', json={'teacher_id': 'T001', 'name': '李教授', 'gender': 'M', 'title': '教授'})
    # 创建课程
    client.post('/api/courses', json={'course_id': 'CS101', 'course_name': '数据结构', 'credits': 4, 'hours': 64, 'type': '必修'})
    # 创建学期
    client.post('/api/semesters', json={'academic_year': '2024-2025', 'semester_name': '第一学期', 'start_date': '2024-09-01', 'end_date': '2025-01-15'})
    # 创建授课
    client.post('/api/teaching', json={'course_id': 'CS101', 'teacher_id': 'T001', 'semester_id': 1, 'classroom': 'A101', 'schedule': '周一 1-2节', 'capacity': 60})
    return client
