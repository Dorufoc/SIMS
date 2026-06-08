"""新功能测试：注册后自动登录 & 强制修改用户名"""
import json


def _safe_json(resp):
    try:
        return json.loads(resp.data)
    except Exception:
        return None


def _get_csrf_headers(client):
    """获取 CSRF token 并返回带 token 的请求头"""
    resp = client.get('/api/csrf-token')
    data = _safe_json(resp)
    token = data.get('token', '') if data else ''
    return {'X-CSRF-Token': token, 'Content-Type': 'application/x-www-form-urlencoded'}


def _register_and_login(client, password, real_name, role, method, value):
    """注册用户（自动登录）并返回响应数据"""
    headers = _get_csrf_headers(client)
    resp = client.post('/register', data={
        'password': password,
        'real_name': real_name,
        'role': role,
        'register_method': method,
        'register_value': value,
    }, headers=headers)
    return _safe_json(resp)


def _clear_rate_limiter():
    """清除登录频率限制计数器，避免跨测试累积"""
    from controller.auth_controller import login
    if hasattr(login, '_attempts'):
        login._attempts.clear()


def _set_username(client, username):
    """设置用户名"""
    csrf_resp = client.get('/api/csrf-token')
    csrf_data = _safe_json(csrf_resp)
    token = csrf_data.get('token', '') if csrf_data else ''
    resp = client.post('/api/set-username',
                       json={'username': username},
                       headers={'X-CSRF-Token': token, 'Content-Type': 'application/json'})
    return _safe_json(resp)


class TestAutoLoginAfterRegister:
    """注册后自动登录功能测试"""

    def test_register_auto_login_student(self, client):
        """注册学生账号后应自动登录，返回 need_set_username=True"""
        data = _register_and_login(client, '123456', '自动登录学生', 'student', 'ref_id', 'S2024099')
        assert data is not None
        assert data['code'] == 0
        assert data['need_set_username'] is True
        assert data['role'] == 'student'
        assert 'redirect_url' in data

        with client.session_transaction() as sess:
            assert 'user_id' in sess
            assert sess['user_role'] == 'student'
            assert sess['username_changed'] is False

    def test_register_auto_login_teacher(self, client):
        """注册教职工账号后应自动登录"""
        data = _register_and_login(client, 'test1234', '自动登录教师', 'teacher', 'phone', '13800001111')
        assert data is not None
        assert data['code'] == 0
        assert data['need_set_username'] is True
        assert data['role'] == 'teacher'

        with client.session_transaction() as sess:
            assert sess['user_role'] == 'teacher'
            assert sess['username_changed'] is False

    def test_register_auto_login_redirect_url(self, client):
        """admin 注册的 redirect_url 应指向 /index"""
        data = _register_and_login(client, 'admin1234', '管理员', 'admin', 'email', 'admin_new@test.com')
        assert data is not None
        assert data['code'] == 0
        assert data['redirect_url'] == '/index'

    def test_register_failure_no_auto_login(self, client):
        """注册失败时不应设置 session"""
        with client.session_transaction() as sess:
            sess.clear()

        headers = _get_csrf_headers(client)
        resp = client.post('/register', data={
            'password': '',
            'real_name': '',
            'role': 'student',
            'register_method': 'ref_id',
            'register_value': '',
        }, headers=headers)
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 1

        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_register_duplicate_no_session_leak(self, client):
        """重复注册时不应修改已有 session"""
        _register_and_login(client, '123456', '用户A', 'student', 'ref_id', 'S2024100')

        with client.session_transaction() as sess:
            sess.clear()

        data = _register_and_login(client, '123456', '用户B', 'student', 'ref_id', 'S2024100')
        assert data is not None
        assert data['code'] == 1

        with client.session_transaction() as sess:
            assert 'user_id' not in sess


class TestForceUsernameChange:
    """强制修改用户名功能测试"""

    def test_register_user_username_changed_is_false(self, client):
        """新注册用户的 username_changed 应为 False"""
        data = _register_and_login(client, 'test1234', '测试', 'student', 'ref_id', 'S2024200')
        assert data is not None
        assert data['code'] == 0

        with client.session_transaction() as sess:
            assert sess['username_changed'] is False

    def test_set_username_updates_username_changed(self, client):
        """设置用户名后 username_changed 应变 True"""
        _register_and_login(client, 'test1234', '测试用户', 'student', 'ref_id', 'S2024201')

        resp = _set_username(client, 'newuser2024')
        assert resp is not None
        assert resp['code'] == 0

        with client.session_transaction() as sess:
            assert sess['username_changed'] is True
            assert sess['user_name'] == 'newuser2024'

    def test_set_username_validation_length(self, client):
        """用户名长度验证"""
        _register_and_login(client, 'test1234', '测试', 'student', 'ref_id', 'S2024202')

        resp = _set_username(client, 'ab')
        assert resp is not None
        assert resp['code'] == 1

        resp = _set_username(client, 'a' * 60)
        assert resp is not None
        assert resp['code'] == 1

    def test_set_username_validation_special_chars(self, client):
        """用户名格式验证：不允许特殊字符"""
        _register_and_login(client, 'test1234', '测试', 'student', 'ref_id', 'S2024203')

        resp = _set_username(client, 'user@name')
        assert resp is not None
        assert resp['code'] == 1

        resp = _set_username(client, 'user name')
        assert resp is not None
        assert resp['code'] == 1

    def test_set_username_duplicate(self, client):
        """设置重复用户名应失败"""
        _register_and_login(client, 'test1234', '用户1', 'student', 'ref_id', 'S2024204')
        resp = _set_username(client, 'user_a')
        assert resp is not None
        assert resp['code'] == 0

        client.get('/logout')
        _register_and_login(client, 'test1234', '用户2', 'student', 'ref_id', 'S2024205')
        resp = _set_username(client, 'user_a')
        assert resp is not None
        assert resp['code'] == 1

    def test_set_username_empty(self, client):
        """空用户名应被拒绝"""
        _register_and_login(client, 'test1234', '测试', 'student', 'ref_id', 'S2024206')

        resp = _set_username(client, '')
        assert resp is not None
        assert resp['code'] == 1


class TestUsernameChangedStatePersistence:
    """用户名修改状态持久化测试"""

    def test_login_reflects_username_changed(self, client):
        """登录时应返回正确的 username_changed 状态"""
        _clear_rate_limiter()
        _register_and_login(client, 'test1234', '状态测试', 'student', 'ref_id', 'S2024300')
        _set_username(client, 'statetest2024')
        client.get('/logout')

        resp = client.post('/login', data={
            'username': 'statetest2024',
            'password': 'test1234',
        })
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 0
        assert data['need_set_username'] is False
        assert data['username_changed'] is True

    def test_login_before_username_change_shows_need(self, client):
        """未修改用户名时登录应返回 need_set_username=True"""
        _register_and_login(client, 'test1234', '未修改用户', 'student', 'ref_id', 'S2024301')
        client.get('/logout')

        from entity.user import User
        from entity.base import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter_by(ref_id='S2024301').first()
        temp_username = user.username
        db.close()

        resp = client.post('/login', data={
            'username': temp_username,
            'password': 'test1234',
        })
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 0
        assert data['need_set_username'] is True

    def test_re_login_without_username_change_still_required(self, client):
        """用户未修改用户名就退出，再次登录仍要求修改"""
        _clear_rate_limiter()
        _register_and_login(client, 'test1234', '反复登录用户', 'student', 'ref_id', 'S2024302')

        from entity.user import User
        from entity.base import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter_by(ref_id='S2024302').first()
        temp_username = user.username
        db.close()

        for i in range(3):
            client.get('/logout')
            resp = client.post('/login', data={
                'username': temp_username,
                'password': 'test1234',
            })
            data = _safe_json(resp)
            assert data is not None
            assert data['code'] == 0, f'第{i+1}次登录失败: {data.get("msg", "")}'
            assert data['need_set_username'] is True, f'第{i+1}次登录应仍要求修改用户名'

        _set_username(client, 'finally_set2024')
        client.get('/logout')
        resp = client.post('/login', data={
            'username': 'finally_set2024',
            'password': 'test1234',
        })
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 0
        assert data['need_set_username'] is False

    def test_middleware_blocks_api_for_unset_username(self, client):
        """未修改用户名的用户调用 API 应被中间件拦截"""
        _register_and_login(client, 'test1234', 'API拦截测试', 'student', 'ref_id', 'S2024303')

        resp = client.get('/api/students')
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 1
        assert data['msg'] == '请先设置用户名'

    def test_middleware_allows_api_after_username_change(self, client):
        """修改用户名后 API 调用应正常"""
        _register_and_login(client, 'test1234', 'API放行测试', 'student', 'ref_id', 'S2024304')
        _set_username(client, 'apitestuser2024')

        resp = client.get('/api/students')
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 0


class TestUserMeEndpoint:
    """user/me API 端点测试"""

    def test_user_me_returns_need_set_username(self, client):
        """未修改用户名的用户调用 /api/user/me 应返回 need_set_username=True"""
        _register_and_login(client, 'test1234', 'Me测试', 'student', 'ref_id', 'S2024400')

        resp = client.get('/api/user/me')
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 0
        assert data['data']['username_changed'] is False
        assert data['data']['need_set_username'] is True

    def test_user_me_after_username_change(self, client):
        """修改用户名后 /api/user/me 应返回 need_set_username=False"""
        _register_and_login(client, 'test1234', 'Me测试2', 'student', 'ref_id', 'S2024401')
        _set_username(client, 'meuser2024')

        resp = client.get('/api/user/me')
        data = _safe_json(resp)
        assert data is not None
        assert data['code'] == 0
        assert data['data']['username_changed'] is True
        assert data['data']['need_set_username'] is False


class TestAdminExemption:
    """管理员不强制修改用户名"""

    def test_admin_not_required_to_set_username(self, client):
        """管理员注册后 API 调用不受用户名修改限制"""
        data = _register_and_login(client, 'admin999', '管理测试', 'admin', 'email', 'admin_test999@test.com')
        assert data is not None
        assert data['code'] == 0

        resp = client.get('/api/students')
        assert resp.status_code == 200
