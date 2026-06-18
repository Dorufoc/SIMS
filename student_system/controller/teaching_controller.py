"""授课管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.teaching_service import TeachingService
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

teaching_bp = Blueprint('teaching', __name__)


@teaching_bp.route('/teaching')
def teaching_page():
    return render_template('teaching.html')


@teaching_bp.route('/api/teaching', methods=['GET'])
def api_teaching():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')

    svc = TeachingService()
    try:
        from sqlalchemy.orm import joinedload
        from entity.teaching import Teaching
        from entity.course import Course
        from entity.teacher import Teacher
        from repository.base import escape_like

        SORT_FIELDS = {
            'teaching_id': Teaching.teaching_id,
            'course_id': Teaching.course_id,
            'teacher_id': Teaching.teacher_id,
            'semester_id': Teaching.semester_id,
            'classroom': Teaching.classroom,
            'schedule': Teaching.schedule,
            'capacity': Teaching.capacity,
            'course_name': Course.course_name,
            'teacher_name': Teacher.name,
        }
        sort_by = request.args.get('sort_by', '')
        sort_order = request.args.get('sort_order', '')
        order_col = SORT_FIELDS.get(sort_by)
        if order_col is not None:
            if sort_order == 'desc':
                order_col = order_col.desc()

        q = svc.repo.db.query(svc.repo.model)

        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []

            # 分离关联表字段和直接字段
            course_name_value = None
            teacher_name_value = None
            simple_filters = []
            for f in filters:
                field = f.get('field', '')
                if field == 'course_name':
                    course_name_value = f.get('value', '')
                elif field == 'teacher_name':
                    teacher_name_value = f.get('value', '')
                else:
                    simple_filters.append(f)

            # 处理 course_name 筛选（关联 Course 表）
            if course_name_value is not None:
                q = q.join(Course, Teaching.course_id == Course.course_id)
                q = q.filter(Course.course_name.like(f'%{escape_like(course_name_value)}%', escape='\\'))

            # 处理 teacher_name 筛选（关联 Teacher 表）
            if teacher_name_value is not None:
                q = q.join(Teacher, Teaching.teacher_id == Teacher.teacher_id)
                q = q.filter(Teacher.name.like(f'%{escape_like(teacher_name_value)}%', escape='\\'))

            # 处理直接字段筛选
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
                column = getattr(Teaching, col_name, None)
                if column is None:
                    continue
                from sqlalchemy import cast, String, Integer
                if isinstance(column.type, Integer) and op in ('contains', 'startswith', 'endswith'):
                    column = cast(column, String)
                if op == 'eq':
                    q = q.filter(column == value)
                elif op == 'neq':
                    q = q.filter(column != value)
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
                elif op == 'between':
                    parts = [v.strip() for v in value.split(',', 1)]
                    if len(parts) == 2 and parts[0] and parts[1]:
                        q = q.filter(column.between(parts[0], parts[1]))

        q = q.options(
            joinedload(svc.repo.model.course),
            joinedload(svc.repo.model.teacher),
            joinedload(svc.repo.model.semester)
        )
        if order_col is not None:
            q = q.order_by(order_col)
        else:
            q = q.order_by(svc.repo.model.teaching_id.desc())

        items, total = svc.repo.paginate(page, page_size, q)
        total_pages = (total + page_size - 1) // page_size
        data = []
        for t in items:
            semester_label = ''
            if t.semester:
                semester_label = f'{t.semester.academic_year} {t.semester.semester_name}'
            data.append({
                'teaching_id': t.teaching_id,
                'course_id': t.course_id,
                'course_name': t.course.course_name if t.course else '',
                'teacher_id': t.teacher_id,
                'teacher_name': t.teacher.name if t.teacher else '',
                'semester_id': t.semester_id,
                'semester_label': semester_label,
                'classroom': t.classroom,
                'schedule': t.schedule,
                'capacity': t.capacity
            })
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@teaching_bp.route('/api/teachers/<teacher_id>/teaching', methods=['GET'])
@teaching_bp.route('/api/teachers/<teacher_id>/teachings', methods=['GET'])
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


@teaching_bp.route('/api/teaching/<int:teaching_id>', methods=['GET'])
def api_get_teaching(teaching_id):
    svc = TeachingService()
    try:
        from sqlalchemy.orm import joinedload
        from entity.teaching import Teaching

        q = svc.repo.db.query(svc.repo.model).options(
            joinedload(svc.repo.model.course),
            joinedload(svc.repo.model.teacher),
            joinedload(svc.repo.model.semester)
        ).filter(svc.repo.model.teaching_id == teaching_id)
        t = q.first()
        if not t:
            return jsonify({'code': 1, 'msg': '授课记录不存在'})
        semester_label = ''
        if t.semester:
            semester_label = f'{t.semester.academic_year} {t.semester.semester_name}'
        data = {
            'teaching_id': t.teaching_id,
            'course_id': t.course_id,
            'course_name': t.course.course_name if t.course else '',
            'teacher_id': t.teacher_id,
            'teacher_name': t.teacher.name if t.teacher else '',
            'semester_id': t.semester_id,
            'semester_label': semester_label,
            'classroom': t.classroom,
            'schedule': t.schedule,
            'capacity': t.capacity
        }
        return jsonify({'code': 0, 'data': data})
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
