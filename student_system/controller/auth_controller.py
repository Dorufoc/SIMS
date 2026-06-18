"""认证 API"""
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, session, redirect, render_template
from middleware.auth_middleware import require_login, csrf_protect
from service.auth_service import AuthService
from config import is_db_available

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/csrf-token', methods=['GET'])
def api_csrf_token():
    """获取 CSRF token"""
    from middleware.auth_middleware import generate_csrf_token
    token = generate_csrf_token()
    return jsonify({'code': 0, 'token': token})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # 登录频率限制：同一 IP 每分钟最多 5 次
    if not hasattr(login, '_attempts'):
        login._attempts = defaultdict(list)

    client_ip = request.remote_addr
    now = datetime.now()
    # 清理过期记录
    login._attempts[client_ip] = [
        t for t in login._attempts[client_ip]
        if t > now - timedelta(minutes=1)
    ]
    if len(login._attempts[client_ip]) >= 5:
        return jsonify({'code': 1, 'msg': '登录尝试过于频繁，请稍后再试'}), 429
    login._attempts[client_ip].append(now)

    identifier = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    # 离线模式：使用本地校验
    if not is_db_available():
        success, msg, user = AuthService.local_login(identifier, password)
        if success:
            session['user_id'] = user['user_id']
            session['user_name'] = user['username']
            session['user_role'] = user['role']
            session['user_ref_id'] = user['ref_id']
            session['user_uuid'] = user['uuid']
            session['username_changed'] = user['username_changed']
            session['offline_mode'] = True
            return jsonify({'code': 0, 'msg': msg, 'role': user['role'],
                            'need_set_username': user['need_set_username'],
                            'username_changed': user['username_changed'],
                            'offline': True})
        return jsonify({'code': 1, 'msg': msg})

    svc = AuthService()
    try:
        success, msg, user = svc.login(identifier, password)
        if success:
            session['user_id'] = user['user_id']
            session['user_name'] = user['username']
            session['user_role'] = user['role']
            session['user_ref_id'] = user['ref_id']
            session['user_uuid'] = user['uuid']
            session['username_changed'] = user['username_changed']
            return jsonify({'code': 0, 'msg': msg, 'role': user['role'],
                            'need_set_username': user['need_set_username'],
                            'username_changed': user['username_changed']})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf_protect
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # 离线模式下禁止注册
    if not is_db_available():
        return jsonify({'code': 1, 'msg': '离线模式下不支持注册，请先配置数据库连接'}), 403

    password = request.form.get('password', '').strip()
    if not password:
        return jsonify({'code': 1, 'msg': '密码不能为空'})
    real_name = request.form.get('real_name', '').strip()
    role = request.form.get('role', 'student').strip()
    register_method = request.form.get('register_method', '').strip()
    register_value = request.form.get('register_value', '').strip()

    svc = AuthService()
    try:
        success, msg, extra = svc.register(password, real_name, role, register_method, register_value)
        if success:
            # 注册成功后自动登录
            session['user_id'] = extra['user_id']
            session['user_name'] = extra['username']
            session['user_role'] = extra['role']
            session['user_ref_id'] = extra['ref_id']
            session['user_uuid'] = extra['uuid']
            session['username_changed'] = extra['username_changed']

            redirect_url = '/index' if extra['role'] == 'admin' else '/my'
            return jsonify({
                'code': 0, 'msg': msg,
                'need_set_username': extra['need_set_username'],
                'role': extra['role'],
                'redirect_url': redirect_url,
            })
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@auth_bp.route('/set-username')
def set_username_page():
    if 'user_id' not in session:
        return redirect('/login')
    force = request.args.get('force', '0') == '1'
    return render_template('set_username.html',
                           current_username=session.get('user_name', ''),
                           force=force)


@auth_bp.route('/api/set-username', methods=['POST'])
@csrf_protect
def api_set_username():
    if 'user_id' not in session:
        return jsonify({'code': 1, 'msg': '未登录'})

    data = request.get_json(silent=True) or {}
    new_username = (data.get('username') or '').strip()

    svc = AuthService()
    try:
        success, msg, result = svc.set_username(session['user_id'], new_username)
        if success:
            session['user_name'] = result
            session['username_changed'] = True
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@auth_bp.route('/api/change-password', methods=['POST'])
@csrf_protect
def api_change_password():
    if 'user_id' not in session:
        return jsonify({'code': 1, 'msg': '未登录'})

    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password') or ''
    new_password = data.get('new_password') or ''

    svc = AuthService()
    try:
        success, msg = svc.change_password(session['user_id'], old_password, new_password)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@auth_bp.route('/api/user/me', methods=['GET'])
def api_user_me():
    """获取当前用户信息"""
    if 'user_id' not in session:
        return jsonify({'code': 1, 'msg': '未登录'}), 401
    return jsonify({'code': 0, 'data': {
        'user_id': session.get('user_id'),
        'username': session.get('user_name', ''),
        'role': session.get('user_role', ''),
        'ref_id': session.get('user_ref_id', ''),
        'username_changed': session.get('username_changed', True),
        'need_set_username': not session.get('username_changed', True),
    }})
