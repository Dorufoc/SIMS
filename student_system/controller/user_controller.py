"""用户管理 API"""
from flask import Blueprint, request, jsonify, render_template, session
from middleware.auth_middleware import require_admin, csrf_protect
from service.user_service import UserService

user_bp = Blueprint('user', __name__)


@user_bp.route('/user_management')
@require_admin
def user_management_page():
    return render_template('user_management.html')


@user_bp.route('/user_management/permissions/<int:user_id>')
@require_admin
def permission_management_page(user_id):
    svc = UserService()
    try:
        user = svc.user_repo.get_by_id(user_id)
        if not user:
            return render_template('permission_management.html', target_user=None)
        return render_template('permission_management.html', target_user={
            'user_id': user.user_id, 'uuid': user.uuid, 'username': user.username,
            'role': user.role, 'ref_id': user.ref_id, 'last_login': str(user.last_login) if user.last_login else None,
            'created_at': str(user.created_at) if user.created_at else None
        })
    finally:
        svc.close()


@user_bp.route('/api/users', methods=['GET'])
@require_admin
def api_users_list():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    filters_json = request.args.get('filters', '')

    svc = UserService()
    try:
        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []
            user_items, total = svc.user_repo.filter_paginate(filters, page, page_size, svc.user_repo.model.created_at.desc())
            items = [(u.user_id, u.uuid, u.username, u.role, u.ref_id, u.last_login, u.created_at) for u in user_items]
        else:
            items, total = svc.get_list(page, page_size, keyword=keyword)
        total_pages = (total + page_size - 1) // page_size
        data = []
        for u in items:
            data.append({
                'user_id': u[0], 'uuid': u[1], 'username': u[2], 'role': u[3],
                'ref_id': u[4], 'last_login': str(u[5]) if u[5] else None,
                'created_at': str(u[6]) if u[6] else None
            })
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@user_bp.route('/api/users', methods=['POST'])
@require_admin
@csrf_protect
def api_create_user():
    data = request.get_json()
    svc = UserService()
    try:
        success, msg = svc.create(data)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@user_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_user(user_id):
    data = request.get_json()
    svc = UserService()
    try:
        success, msg = svc.update(user_id, data)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@user_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_user(user_id):
    if 'user_id' in session and session['user_id'] == user_id:
        return jsonify({'code': 1, 'msg': '不能删除自己的账号'})

    svc = UserService()
    try:
        svc.delete(user_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()


@user_bp.route('/api/users/<int:user_id>/permissions', methods=['GET'])
@require_admin
def api_user_permissions(user_id):
    svc = UserService()
    try:
        permissions = svc.get_permissions(user_id)
        data = [{'table_name': p.table_name, 'permission_code': p.permission_code} for p in permissions]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@user_bp.route('/api/users/<int:user_id>/permissions', methods=['PUT'])
@require_admin
@csrf_protect
def api_set_user_permissions(user_id):
    data = request.get_json()
    permissions_list = data.get('permissions', [])

    svc = UserService()
    try:
        success, msg = svc.set_permissions(user_id, permissions_list)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@user_bp.route('/api/tables', methods=['GET'])
@require_admin
def api_tables_list():
    svc = UserService()
    try:
        tables = svc.get_tables()
        return jsonify({'code': 0, 'data': tables})
    finally:
        svc.close()
