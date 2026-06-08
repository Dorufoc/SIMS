"""院系管理 API"""
import logging
from flask import Blueprint, request, jsonify, render_template
from service.department_service import DepartmentService
from repository.base import escape_like
from middleware.auth_middleware import require_login, require_admin, csrf_protect

dept_bp = Blueprint('department', __name__)


@dept_bp.route('/departments')
def departments_page():
    return render_template('departments.html')


@dept_bp.route('/api/departments', methods=['GET'])
@require_login
def api_departments():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')
    keyword = request.args.get('keyword', '').strip()
    simple = request.args.get('simple', '')

    svc = DepartmentService()
    try:
        if simple == '1':
            depts = svc.get_all()
            return jsonify([{'dept_id': d.dept_id, 'dept_name': d.dept_name} for d in depts])

        if keyword:
            from entity.department import Department
            q = svc.repo.db.query(Department).filter(Department.dept_name.like(f'%{keyword}%'))
            items, total = svc.repo.paginate(page, page_size, q)
        else:
            items, total = svc.get_list(page, page_size)

        total_pages = (total + page_size - 1) // page_size
        data = [{'dept_id': d.dept_id, 'dept_name': d.dept_name, 'dean': d.dean, 'phone': d.phone} for d in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@dept_bp.route('/api/departments', methods=['POST'])
@require_login
@require_admin
@csrf_protect
def api_create_department():
    data = request.get_json()
    svc = DepartmentService()
    try:
        svc.create({'dept_name': data.get('dept_name', ''), 'dean': data.get('dean', ''), 'phone': data.get('phone', '')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except (ValueError, KeyError) as e:
        return jsonify({'code': 1, 'msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logging.exception('创建院系失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@dept_bp.route('/api/departments/<int:dept_id>', methods=['PUT'])
@require_login
@require_admin
@csrf_protect
def api_update_department(dept_id):
    data = request.get_json()
    svc = DepartmentService()
    try:
        result = svc.update(dept_id, {'dept_name': data.get('dept_name', ''), 'dean': data.get('dean', ''), 'phone': data.get('phone', '')})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '院系不存在'})
    finally:
        svc.close()


@dept_bp.route('/api/departments/<int:dept_id>', methods=['DELETE'])
@require_login
@require_admin
@csrf_protect
def api_delete_department(dept_id):
    svc = DepartmentService()
    try:
        svc.delete(dept_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()
