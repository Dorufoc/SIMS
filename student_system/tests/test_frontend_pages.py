"""前端页面可访问性测试"""
import json


PUBLIC_PAGES = ['/login', '/register']

PROTECTED_PAGES = [
    '/',
    '/manage',
    '/add',
    '/my',
    '/teachers',
    '/courses',
    '/classes',
    '/departments',
    '/majors',
    '/dorm_rooms',
    '/dorm_assignments',
    '/statistics',
    '/query',
    '/set-username',
]


class TestPublicPages:
    """公开页面测试（无需登录）"""
    
    def test_login_page(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200
        assert b'login' in resp.data.lower() or b'\xe7\x99\xbb\xe5\xbd\x95' in resp.data
    
    def test_register_page(self, client):
        resp = client.get('/register')
        assert resp.status_code == 200


class TestProtectedPagesUnauthenticated:
    """受保护页面：未登录应重定向"""
    
    def test_index_redirects(self, client):
        resp = client.get('/')
        assert resp.status_code in (302, 401)
    
    def test_manage_redirects(self, client):
        resp = client.get('/manage')
        assert resp.status_code in (302, 401)
    
    def test_add_student_redirects(self, client):
        resp = client.get('/add')
        assert resp.status_code in (302, 401)
    
    def test_my_info_redirects(self, client):
        resp = client.get('/my')
        assert resp.status_code in (302, 401)
    
    def test_teachers_redirects(self, client):
        resp = client.get('/teachers')
        assert resp.status_code in (302, 401)
    
    def test_courses_redirects(self, client):
        resp = client.get('/courses')
        assert resp.status_code in (302, 401)
    
    def test_classes_redirects(self, client):
        resp = client.get('/classes')
        assert resp.status_code in (302, 401)
    
    def test_departments_redirects(self, client):
        resp = client.get('/departments')
        assert resp.status_code in (302, 401)
    
    def test_majors_redirects(self, client):
        resp = client.get('/majors')
        assert resp.status_code in (302, 401)
    
    def test_dorm_rooms_redirects(self, client):
        resp = client.get('/dorm_rooms')
        assert resp.status_code in (302, 401)
    
    def test_dorm_assignments_redirects(self, client):
        resp = client.get('/dorm_assignments')
        assert resp.status_code in (302, 401)
    
    def test_statistics_redirects(self, client):
        resp = client.get('/statistics')
        assert resp.status_code in (302, 401)
    
    def test_query_redirects(self, client):
        resp = client.get('/query')
        assert resp.status_code in (302, 401)
    
    def test_username_page_redirects(self, client):
        resp = client.get('/set-username')
        assert resp.status_code in (302, 401)


class TestProtectedPagesAuthenticated:
    """受保护页面：已登录可访问"""
    
    def test_index_page(self, auth_client):
        resp = auth_client.get('/')
        assert resp.status_code == 200
    
    def test_manage_page(self, auth_client):
        resp = auth_client.get('/manage')
        assert resp.status_code == 200
    
    def test_add_student_page(self, auth_client):
        resp = auth_client.get('/add')
        assert resp.status_code == 200
    
    def test_my_info_page(self, auth_client):
        resp = auth_client.get('/my')
        assert resp.status_code in (200, 302)
    
    def test_teachers_page(self, auth_client):
        resp = auth_client.get('/teachers')
        assert resp.status_code == 200
    
    def test_courses_page(self, auth_client):
        resp = auth_client.get('/courses')
        assert resp.status_code == 200
    
    def test_classes_page(self, auth_client):
        resp = auth_client.get('/classes')
        assert resp.status_code == 200
    
    def test_departments_page(self, auth_client):
        resp = auth_client.get('/departments')
        assert resp.status_code == 200
    
    def test_majors_page(self, auth_client):
        resp = auth_client.get('/majors')
        assert resp.status_code == 200
    
    def test_dorm_rooms_page(self, auth_client):
        resp = auth_client.get('/dorm_rooms')
        assert resp.status_code == 200
    
    def test_dorm_assignments_page(self, auth_client):
        resp = auth_client.get('/dorm_assignments')
        assert resp.status_code == 200
    
    def test_statistics_page(self, auth_client):
        resp = auth_client.get('/statistics')
        assert resp.status_code == 200
    
    def test_query_page(self, auth_client):
        resp = auth_client.get('/query')
        assert resp.status_code == 200
    
    def test_username_page(self, auth_client):
        resp = auth_client.get('/set-username')
        assert resp.status_code == 200
    
    # Admin-only pages
    def test_user_management_page(self, auth_client):
        resp = auth_client.get('/user_management')
        assert resp.status_code == 200
