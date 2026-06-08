"""选课管理 API"""
from flask import Blueprint, request, jsonify
from service.enrollment_service import EnrollmentService
from middleware.auth_middleware import require_login, csrf_protect

enrollment_bp = Blueprint('enrollment', __name__)


@enrollment_bp.route('/api/enrollment/available', methods=['GET'])
@require_login
def api_available_courses():
    student_id = request.args.get('student_id', '')
    svc = EnrollmentService()
    try:
        courses = svc.get_available_courses(student_id)
        data = [{'teaching_id': c.teaching_id, 'course_id': c.course_id, 'teacher_id': c.teacher_id,
                 'semester_id': c.semester_id, 'classroom': c.classroom, 'schedule': c.schedule} for c in courses]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@enrollment_bp.route('/api/enrollment', methods=['POST'])
@require_login
@csrf_protect
def api_enroll():
    data = request.get_json()
    svc = EnrollmentService()
    try:
        success, msg = svc.enroll(data.get('student_id', ''), data.get('teaching_id', 0))
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@enrollment_bp.route('/api/enrollment/<int:enroll_id>/drop', methods=['POST'])
@require_login
@csrf_protect
def api_drop(enroll_id):
    svc = EnrollmentService()
    try:
        success, msg = svc.drop(enroll_id)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@enrollment_bp.route('/api/students/<student_id>/enrollment', methods=['GET'])
@require_login
def api_student_enrollments(student_id):
    svc = EnrollmentService()
    try:
        enrollments = svc.get_student_enrollments(student_id)
        data = [{'enroll_id': e.enroll_id, 'student_id': e.student_id,
                 'teaching_id': e.teaching_id, 'score': float(e.score) if e.score else None,
                 'grade_point': float(e.grade_point) if e.grade_point else None,
                 'status': e.status} for e in enrollments]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()
