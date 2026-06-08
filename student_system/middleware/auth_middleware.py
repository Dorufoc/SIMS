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
    """要求管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 1, 'msg': '请先登录'}), 401
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
