"""课程管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.course_service import CourseService
from repository.base import escape_like
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

course_bp = Blueprint('course', __name__)


@course_bp.route('/courses')
def courses_page():
    return render_template('courses.html')


@course_bp.route('/api/courses', methods=['GET'])
@require_login
def api_courses():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()

    svc = CourseService()
    try:
        from entity.course import Course
        q = svc.repo.db.query(Course)
        if keyword:
            q = q.filter(
                (Course.course_id.like(f'%{escape_like(keyword)}%', escape='\\')) |
                (Course.course_name.like(f'%{escape_like(keyword)}%', escape='\\'))
            )
        q = q.order_by(Course.course_id)
        items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{'course_id': c.course_id, 'course_name': c.course_name, 'credits': float(c.credits or 0),
                 'hours': c.hours, 'type': c.type, 'dept_id': c.dept_id} for c in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@course_bp.route('/api/courses', methods=['POST'])
@require_admin
@csrf_protect
def api_create_course():
    data = request.get_json()
    svc = CourseService()
    try:
        svc.create({'course_id': data.get('course_id', ''), 'course_name': data.get('course_name', ''),
                    'credits': data.get('credits'), 'hours': data.get('hours'), 'type': data.get('type', '必修'),
                    'dept_id': data.get('dept_id')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except (ValueError, KeyError) as e:
        return jsonify({'code': 1, 'msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logging.exception('创建课程失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@course_bp.route('/api/courses/<course_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_course(course_id):
    data = request.get_json()
    svc = CourseService()
    try:
        result = svc.update(course_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '课程不存在'})
    finally:
        svc.close()


@course_bp.route('/api/courses/<course_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_course(course_id):
    svc = CourseService()
    try:
        svc.delete(course_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()
