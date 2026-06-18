"""培养计划 API"""
import logging
from flask import Blueprint, request, jsonify
from service.curriculum_service import CurriculumService
from middleware.auth_middleware import require_login, csrf_protect

curriculum_bp = Blueprint('curriculum', __name__)


@curriculum_bp.route('/api/curriculum', methods=['GET'])
@require_login
def api_curriculum():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    major_id = request.args.get('major_id', type=int)
    enrollment_year = request.args.get('enrollment_year', type=int)

    svc = CurriculumService()
    try:
        if major_id and enrollment_year:
            plans = svc.get_by_student(major_id, enrollment_year)
            data = [{'plan_id': p.plan_id, 'major_id': p.major_id, 'enrollment_year': p.enrollment_year,
                     'course_id': p.course_id, 'course_type': p.course_type,
                     'recommended_term': p.recommended_term, 'min_grade': float(p.min_grade) if p.min_grade else None,
                     'is_core': p.is_core, 'remark': p.remark} for p in plans]
            return jsonify({'code': 0, 'data': data})

        items, total = svc.get_list(page, page_size)
        total_pages = (total + page_size - 1) // page_size
        data = [{'plan_id': p.plan_id, 'major_id': p.major_id, 'enrollment_year': p.enrollment_year,
                 'course_id': p.course_id, 'course_type': p.course_type,
                 'recommended_term': p.recommended_term, 'is_core': p.is_core} for p in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@curriculum_bp.route('/api/students/<student_id>/curriculum', methods=['GET'])
@require_login
def api_student_curriculum(student_id):
    from entity.student import Student
    svc = CurriculumService()
    try:
        student = svc.repo.db.query(Student).filter(Student.student_id == student_id).first()
        if not student or not student.class_:
            return jsonify({'code': 0, 'data': []})

        major_id = student.class_.major_id
        enrollment_year = student.enrollment_year
        plans = svc.get_by_student(major_id, enrollment_year)
        data = [{'plan_id': p.plan_id, 'major_id': p.major_id, 'enrollment_year': p.enrollment_year,
                 'course_id': p.course_id, 'course_type': p.course_type,
                 'recommended_term': p.recommended_term, 'is_core': p.is_core} for p in plans]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@curriculum_bp.route('/api/curriculum', methods=['POST'])
@require_login
@csrf_protect
def api_create_curriculum():
    data = request.get_json()
    svc = CurriculumService()
    try:
        svc.create({'major_id': data.get('major_id'), 'enrollment_year': data.get('enrollment_year'),
                    'course_id': data.get('course_id', ''), 'course_type': data.get('course_type', '必修'),
                    'recommended_term': data.get('recommended_term', ''), 'is_core': data.get('is_core', False),
                    'remark': data.get('remark', '')})
        return jsonify({'code': 0, 'msg': '添加成功'})
    except Exception as e:
        logging.exception('添加培养计划失败')
        return jsonify({'code': 1, 'msg': '添加失败，请稍后重试'})
    finally:
        svc.close()


@curriculum_bp.route('/api/curriculum/<int:plan_id>', methods=['PUT'])
@require_login
@csrf_protect
def api_update_curriculum(plan_id):
    data = request.get_json()
    svc = CurriculumService()
    try:
        result = svc.update(plan_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '记录不存在'})
    finally:
        svc.close()


@curriculum_bp.route('/api/curriculum/<int:plan_id>', methods=['DELETE'])
@require_login
@csrf_protect
def api_delete_curriculum(plan_id):
    svc = CurriculumService()
    try:
        existing = svc.repo.get_by_id(plan_id)
        if not existing:
            return jsonify({'code': 1, 'msg': '记录不存在'}), 404
        svc.delete(plan_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()
