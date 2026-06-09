"""
认证和权限中间件
提供 @require_login, @require_admin, @require_permission 装饰器
"""
import secrets
from functools import wraps
from flask import session, jsonify, redirect, request, current_app
from repository.user_repo import UserRepo
from repository.user_permission_repo import UserPermissionRepo
from utils.permission_utils import parse_permission_code, PERM_READ, PERM_WRITE, PERM_ADMIN


def require_login(f):
    """要求登录的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 1, 'msg': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """要求管理员权限的装饰器（离线模式下允许任何已登录用户访问）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 1, 'msg': '请先登录'}), 401
        # 离线模式：数据库不可用时，允许任何已登录用户访问管理功能
        from config import is_db_available
        if not is_db_available():
            return f(*args, **kwargs)
        if session.get('user_role') != 'admin':
            return jsonify({'code': 1, 'msg': '仅超级管理员可访问'}), 403
        return f(*args, **kwargs)
    return decorated_function


def require_permission(table_name, required_perm):
    """要求指定表权限的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'code': 1, 'msg': '请先登录'}), 401

            user_role = session.get('user_role')
            if user_role == 'admin':
                return f(*args, **kwargs)

            user_uuid = session.get('user_uuid')
            if not user_uuid:
                return jsonify({'code': 1, 'msg': '权限不足'}), 403

            repo = UserPermissionRepo()
            try:
                perm = repo.find_by_user_and_table(user_uuid, table_name)
                if not perm:
                    return jsonify({'code': 1, 'msg': '权限不足'}), 403
                has_read, has_write, has_admin = parse_permission_code(perm.permission_code)

                if required_perm == PERM_READ:
                    ok = has_read
                elif required_perm == PERM_WRITE:
                    ok = has_write
                elif required_perm == PERM_ADMIN:
                    ok = has_admin
                else:
                    ok = False

                if not ok:
                    return jsonify({'code': 1, 'msg': '权限不足'}), 403
            finally:
                repo.close()

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_csrf_token():
    """生成 CSRF token 并存入 session"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def csrf_protect(f):
    """CSRF 保护装饰器 —— 用于 POST/PUT/PATCH/DELETE 端点（基于 X-CSRF-Token 请求头）"""
    from flask import request, jsonify, current_app
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return f(*args, **kwargs)

        # 测试环境下跳过 CSRF 验证
        if current_app.config.get('TESTING'):
            return f(*args, **kwargs)

        token = request.headers.get('X-CSRF-Token', '')
        session_token = session.get('_csrf_token', '')

        if not token or not session_token or not secrets.compare_digest(token, session_token):
            return jsonify({'code': 1, 'msg': 'CSRF 验证失败'}), 403

        return f(*args, **kwargs)
    return decorated_function


def register_global_interceptor(app):
    """注册全局 before_request 拦截器"""

    @app.before_request
    def check_login():
        """未登录用户拦截，白名单路由放行；临时用户名强制跳转"""
        white_list = ['/login', '/register', '/api/csrf-token']
        path = request.path

        # 白名单路由放行
        if path in white_list or path.startswith('/static'):
            return None

        # ── 离线模式全局拦截 ──
        from config import is_db_available
        if not is_db_available():
            # 未登录 → 重定向到登录页
            if 'user_id' not in session:
                if path.startswith('/api/'):
                    return jsonify({'code': 1, 'msg': '请先登录'}), 401
                return redirect('/login')

            # 已登录 → 仅允许访问 /settings 和基础 API
            offline_allowed_pages = ['/settings', '/login', '/register', '/logout']
            offline_allowed_api_prefixes = ['/api/settings', '/api/csrf-token', '/api/user/me']
            offline_allowed_apis = ['/api/csrf-token', '/api/user/me']

            if path.startswith('/api/'):
                if path in offline_allowed_apis or any(path.startswith(p) for p in offline_allowed_api_prefixes):
                    return None
                return jsonify({'code': 1, 'msg': '离线模式下仅支持设置页面功能'}), 403

            # 非 API 页面请求
            if path not in offline_allowed_pages and not path.startswith('/static'):
                return redirect('/settings')
            return None

        # API 路径：未登录返回 JSON 401（不重定向）
        if path.startswith('/api/') and 'user_id' not in session:
            return jsonify({'code': 1, 'msg': '请先登录'}), 401

        # 非 API 路径：检查 session 中是否有 user_id，否则重定向到登录页
        if 'user_id' not in session:
            return redirect('/login')

        # 学生/教职工未完成用户名修改时：
        #   - 页面请求：放行（页面内模态窗口负责拦截）
        #   - API 请求（非白名单）：拦截并返回 JSON
        user_role = session.get('user_role', '')
        if user_role != 'admin' and not session.get('username_changed', True):
            if path.startswith('/api/') and path not in ('/api/set-username', '/api/csrf-token', '/api/user/me'):
                return jsonify({'code': 1, 'msg': '请先设置用户名', 'need_set_username': True}), 403

        # ===== 非管理员全局路由拦截 =====
        # 学生和教职工仅能访问个人档案页面及自服务 API
        if user_role not in ('admin', ''):
            # 页面路由白名单：非管理员只能访问这几个页面
            page_whitelist = ['/my', '/login', '/register', '/logout', '/set-username']
            is_page_request = not path.startswith('/api/') and not path.startswith('/static')
            if is_page_request:
                if path not in page_whitelist:
                    return redirect('/my')

            # API 路由白名单
            if path.startswith('/api/'):
                # 完全开放的 API
                open_apis = ['/api/csrf-token', '/api/user/me', '/api/change-password',
                            '/api/set-username']
                if path in open_apis or path.startswith('/api/my/'):
                    return None

                # 自数据 API：学生读取自身 /api/students/<自己的id>/*
                ref_id = session.get('user_ref_id', '')
                if user_role == 'student' and ref_id:
                    student_api_prefix = f'/api/students/{ref_id}'
                    if path == student_api_prefix or path.startswith(student_api_prefix + '/'):
                        return None

                # 自数据 API：教师读取自身 /api/teachers/<自己的id>/*
                if user_role == 'teacher' and ref_id:
                    teacher_api_prefix = f'/api/teachers/{ref_id}'
                    if path == teacher_api_prefix or path.startswith(teacher_api_prefix + '/'):
                        return None

                return jsonify({'code': 1, 'msg': '权限不足'}), 403
