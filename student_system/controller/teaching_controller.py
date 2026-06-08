"""授课管理 API"""
from flask import Blueprint, request, jsonify
from service.teaching_service import TeachingService
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

teaching_bp = Blueprint('teaching', __name__)


@teaching_bp.route('/api/teaching', methods=['GET'])
def api_teaching():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    svc = TeachingService()
    try:
        items, total = svc.get_list(page, page_size)
        total_pages = (total + page_size - 1) // page_size
        data = [{'teaching_id': t.teaching_id, 'course_id': t.course_id,
                 'teacher_id': t.teacher_id, 'semester_id': t.semester_id,
                 'classroom': t.classroom, 'schedule': t.schedule, 'capacity': t.capacity} for t in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@teaching_bp.route('/api/teachers/<teacher_id>/teaching', methods=['GET'])
def api_teacher_teaching(teacher_id):
    svc = TeachingService()
    try:
        teachings = svc.get_by_teacher(teacher_id)
        data = [{'teaching_id': t.teaching_id, 'course_id': t.course_id,
                 'teacher_id': t.teacher_id, 'semester_id': t.semester_id,
                 'classroom': t.classroom, 'schedule': t.schedule, 'capacity': t.capacity} for t in teachings]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@teaching_bp.route('/api/teaching', methods=['POST'])
@require_admin
@csrf_protect
def api_create_teaching():
    data = request.get_json()
    svc = TeachingService()
    try:
        svc.create({'course_id': data.get('course_id', ''), 'teacher_id': data.get('teacher_id', ''),
                    'semester_id': data.get('semester_id'), 'classroom': data.get('classroom', ''),
                    'schedule': data.get('schedule', ''), 'capacity': data.get('capacity', 30)})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except Exception as e:
        logging.exception('创建教学安排失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@teaching_bp.route('/api/teaching/<int:teaching_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_teaching(teaching_id):
    data = request.get_json()
    svc = TeachingService()
    try:
        result = svc.update(teaching_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '授课记录不存在'})
    finally:
        svc.close()


@teaching_bp.route('/api/teaching/<int:teaching_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_teaching(teaching_id):
    svc = TeachingService()
    try:
        svc.delete(teaching_id)
        return jsonify({'code': 0, 'msg': '取消授课成功'})
    finally:
        svc.close()
