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
    filters_json = request.args.get('filters', '')

    svc = CourseService()
    try:
        from entity.course import Course
        from entity.department import Department
        from sqlalchemy.orm import joinedload

        SORT_FIELDS = {
            'course_id': Course.course_id,
            'course_name': Course.course_name,
            'credits': Course.credits,
            'hours': Course.hours,
            'type': Course.type,
            'dept_name': Department.dept_name,
        }
        sort_by = request.args.get('sort_by', '')
        sort_order = request.args.get('sort_order', '')
        order_col = SORT_FIELDS.get(sort_by)
        if order_col is not None:
            if sort_order == 'desc':
                order_col = order_col.desc()

        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []

            # 分离 dept_name 关联表筛选字段
            dept_name_value = None
            simple_filters = []
            for f in filters:
                if f.get('field') == 'dept_name':
                    dept_name_value = f.get('value', '')
                else:
                    simple_filters.append(f)

            if dept_name_value:
                from entity.department import Department
                q = svc.repo.db.query(Course).join(Department, Course.dept_id == Department.dept_id)
                q = q.filter(Department.dept_name.like(f'%{escape_like(dept_name_value)}%', escape='\\'))
                # 处理剩余的普通字段筛选
                FIELD_MAP = getattr(svc.repo, 'field_map', {})
                for f in simple_filters:
                    field = f.get('field', '')
                    op = f.get('op', 'eq')
                    value = f.get('value', '')
                    if not field:
                        continue
                    if FIELD_MAP and field not in FIELD_MAP:
                        continue
                    col_name = FIELD_MAP.get(field, field)
                    column = getattr(Course, col_name, None)
                    if column is None:
                        continue
                    if op == 'eq':
                        q = q.filter(column == value)
                    elif op == 'contains':
                        q = q.filter(column.like(f'%{escape_like(value)}%', escape='\\'))
                    elif op == 'startswith':
                        q = q.filter(column.like(f'{escape_like(value)}%', escape='\\'))
                    elif op == 'endswith':
                        q = q.filter(column.like(f'%{escape_like(value)}', escape='\\'))
                    elif op == 'gt':
                        q = q.filter(column > value)
                    elif op == 'gte':
                        q = q.filter(column >= value)
                    elif op == 'lt':
                        q = q.filter(column < value)
                    elif op == 'lte':
                        q = q.filter(column <= value)
                if order_col is not None:
                    q = q.order_by(order_col)
                else:
                    q = q.order_by(Course.course_id)
                items, total = svc.repo.paginate(page, page_size, q)
            else:
                order_by = order_col if order_col is not None else Course.course_id
                items, total = svc.repo.filter_paginate(simple_filters, page, page_size, order_by)
        else:
            q = svc.repo.db.query(Course).options(joinedload(Course.department))
            if keyword:
                q = q.filter(
                    (Course.course_id.like(f'%{escape_like(keyword)}%', escape='\\')) |
                    (Course.course_name.like(f'%{escape_like(keyword)}%', escape='\\'))
                )
            if order_col is not None:
                q = q.order_by(order_col)
            else:
                q = q.order_by(Course.course_id)
            items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{'course_id': c.course_id, 'course_name': c.course_name, 'credits': float(c.credits or 0),
                 'hours': c.hours, 'type': c.type, 'dept_id': c.dept_id,
                 'dept_name': c.department.dept_name if c.department else ''} for c in items]
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


@course_bp.route('/api/courses/<course_id>', methods=['GET'])
@require_login
def api_course_detail(course_id):
    svc = CourseService()
    try:
        from entity.course import Course
        from entity.department import Department
        from sqlalchemy.orm import joinedload
        course = svc.repo.db.query(Course).options(joinedload(Course.department)).filter(Course.course_id == course_id).first()
        if not course:
            return jsonify({'code': 1, 'msg': '课程不存在'})
        return jsonify({'code': 0, 'data': {
            'course_id': course.course_id,
            'course_name': course.course_name,
            'credits': float(course.credits) if course.credits else 0,
            'hours': course.hours,
            'type': course.type,
            'dept_id': course.dept_id,
            'dept_name': course.department.dept_name if course.department else '',
        }})
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
