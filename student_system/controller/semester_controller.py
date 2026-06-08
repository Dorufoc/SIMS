"""学期管理 API"""
from flask import Blueprint, request, jsonify
from service.semester_service import SemesterService
from middleware.auth_middleware import require_login, csrf_protect
import logging

semester_bp = Blueprint('semester', __name__)


@semester_bp.route('/api/semesters', methods=['GET'])
@require_login
def api_semesters():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    svc = SemesterService()
    try:
        items, total = svc.get_list(page, page_size)
        total_pages = (total + page_size - 1) // page_size
        data = [{'semester_id': s.semester_id, 'academic_year': s.academic_year,
                 'semester_name': s.semester_name, 'start_date': str(s.start_date),
                 'end_date': str(s.end_date), 'is_current': s.is_current} for s in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@semester_bp.route('/api/semesters', methods=['POST'])
@require_login
@csrf_protect
def api_create_semester():
    data = request.get_json()
    svc = SemesterService()
    try:
        from datetime import date
        svc.create({'academic_year': data.get('academic_year', ''),
                    'semester_name': data.get('semester_name', ''),
                    'start_date': data.get('start_date', str(date.today())),
                    'end_date': data.get('end_date', str(date.today()))})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except Exception as e:
        logging.exception('创建学期失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@semester_bp.route('/api/semesters/<int:semester_id>', methods=['PUT'])
@require_login
@csrf_protect
def api_update_semester(semester_id):
    data = request.get_json()
    svc = SemesterService()
    try:
        result = svc.update(semester_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '学期不存在'})
    finally:
        svc.close()


@semester_bp.route('/api/semesters/<int:semester_id>', methods=['DELETE'])
@require_login
@csrf_protect
def api_delete_semester(semester_id):
    svc = SemesterService()
    try:
        svc.delete(semester_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()


@semester_bp.route('/api/semesters/<int:semester_id>/set_current', methods=['POST'])
@require_login
@csrf_protect
def api_set_current_semester(semester_id):
    svc = SemesterService()
    try:
        svc.set_current(semester_id)
        return jsonify({'code': 0, 'msg': '设置当前学期成功'})
    finally:
        svc.close()
