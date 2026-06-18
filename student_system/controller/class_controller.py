"""班级管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.class_service import ClassService
from repository.base import escape_like
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

class_bp = Blueprint('class', __name__)


@class_bp.route('/classes')
def classes_page():
    return render_template('classes.html')


@class_bp.route('/api/classes', methods=['GET'])
@require_login
def api_classes():
    major_id = request.args.get('major_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    filters_json = request.args.get('filters', '')

    svc = ClassService()
    try:
        from entity.class_ import Class
        from entity.major import Major
        from entity.department import Department
        from sqlalchemy.orm import joinedload
        from sqlalchemy import func

        SORT_FIELDS = {
            'class_name': Class.class_name,
            'major_id': Class.major_id,
            'enrollment_year': Class.enrollment_year,
            'advisor': Class.advisor,
            'class_id': Class.class_id,
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

            # 分离特殊筛选字段（关联表的字段或计算字段）
            major_name_value = None
            dept_name_value = None
            student_count_filters = []
            simple_filters = []
            for f in filters:
                field = f.get('field', '')
                if field == 'major_name':
                    major_name_value = f.get('value', '')
                elif field == 'dept_name':
                    dept_name_value = f.get('value', '')
                elif field == 'student_count':
                    student_count_filters.append(f)
                else:
                    simple_filters.append(f)

            has_special = major_name_value or dept_name_value or student_count_filters
            # 如果存在特殊筛选字段，需要手动构建带 JOIN / 子查询的查询
            if has_special:
                q = svc.repo.db.query(Class)

                # 处理 major_name / dept_name 关联表筛选
                if major_name_value or dept_name_value:
                    q = q.join(Major, Class.major_id == Major.major_id)
                    if dept_name_value:
                        q = q.join(Department, Major.dept_id == Department.dept_id)
                    if major_name_value:
                        q = q.filter(Major.major_name.like(f'%{escape_like(major_name_value)}%', escape='\\'))
                    if dept_name_value:
                        q = q.filter(Department.dept_name.like(f'%{escape_like(dept_name_value)}%', escape='\\'))

                # 处理 student_count 计算字段筛选（使用子查询统计学生人数）
                if student_count_filters:
                    from entity.student import Student
                    from sqlalchemy import func
                    student_subq = svc.repo.db.query(
                        Student.class_id,
                        func.count(Student.student_id).label('cnt')
                    ).group_by(Student.class_id).subquery()
                    q = q.outerjoin(student_subq, Class.class_id == student_subq.c.class_id)

                    for f in student_count_filters:
                        op = f.get('op', 'eq')
                        value = f.get('value', '')
                        col = func.coalesce(student_subq.c.cnt, 0)
                        if op == 'eq':
                            q = q.filter(col == value)
                        elif op == 'neq':
                            q = q.filter(col != value)
                        elif op == 'gt':
                            q = q.filter(col > value)
                        elif op == 'gte':
                            q = q.filter(col >= value)
                        elif op == 'lt':
                            q = q.filter(col < value)
                        elif op == 'lte':
                            q = q.filter(col <= value)
                        elif op == 'between':
                            parts = [v.strip() for v in str(value).split(',', 1)]
                            if len(parts) == 2 and parts[0] and parts[1]:
                                q = q.filter(col.between(parts[0], parts[1]))

                # 处理剩余的标准字段筛选
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
                    column = getattr(Class, col_name, None)
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
                    q = q.order_by(Class.class_name)
                items, total = svc.repo.paginate(page, page_size, q)
                # 重新附加 major 关系（因 JOIN 可能覆盖了 joinedload 的加载）
                if items:
                    major_ids = list(set(c.major_id for c in items))
                    if major_ids:
                        majors_map = {m.major_id: m for m in svc.repo.db.query(Major).filter(Major.major_id.in_(major_ids)).all()}
                        # 批量查询院系名称
                        dept_ids = list(set(m.dept_id for m in majors_map.values()))
                        dept_name_map = {}
                        if dept_ids:
                            dept_rows = svc.repo.db.query(Department.dept_id, Department.dept_name).filter(Department.dept_id.in_(dept_ids)).all()
                            dept_name_map = {d.dept_id: d.dept_name for d in dept_rows}
                        for c in items:
                            if c.major_id in majors_map:
                                c.major = majors_map[c.major_id]
                                # 附加 dept_name 属性以供后续使用
                                c.dept_name = dept_name_map.get(majors_map[c.major_id].dept_id, '')
            else:
                order_by = order_col if order_col is not None else Class.class_name
                items, total = svc.repo.filter_paginate(simple_filters, page, page_size, order_by)
        else:
            q = svc.repo.db.query(Class).options(joinedload(Class.major))
            if major_id:
                q = q.filter(Class.major_id == major_id)
            if keyword:
                q = q.filter(Class.class_name.like(f'%{escape_like(keyword)}%', escape='\\'))
            if order_col is not None:
                q = q.order_by(order_col)
            else:
                q = q.order_by(Class.class_name)
            items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size

        # 批量查询各班级的学生人数
        class_ids = [c.class_id for c in items]
        student_counts = {}
        if class_ids:
            from entity.student import Student
            count_q = svc.repo.db.query(Student.class_id, func.count(Student.student_id))
            count_q = count_q.filter(Student.class_id.in_(class_ids))
            count_q = count_q.group_by(Student.class_id)
            for row in count_q.all():
                student_counts[row[0]] = row[1]

        # 批量查询各班级的所属院系名称
        dept_name_map = {}
        if class_ids:
            dept_q = svc.repo.db.query(
                Class.class_id, Department.dept_name
            ).join(Major, Class.major_id == Major.major_id
            ).join(Department, Major.dept_id == Department.dept_id
            ).filter(Class.class_id.in_(class_ids)).all()
            dept_name_map = {row.class_id: row.dept_name for row in dept_q}

        # 批量查询教师信息（用于解析 advisor 为姓名）
        teacher_ids = [c.advisor for c in items if c.advisor]
        teacher_name_map = {}
        if teacher_ids:
            from entity.teacher import Teacher
            teachers = svc.repo.db.query(Teacher.teacher_id, Teacher.name).filter(Teacher.teacher_id.in_(teacher_ids)).all()
            teacher_name_map = {t.teacher_id: t.name for t in teachers}

        data = []
        for c in items:
            data.append({
                'class_id': c.class_id,
                'class_name': c.class_name,
                'major_id': c.major_id,
                'major_name': c.major.major_name if c.major else '',
                'dept_name': dept_name_map.get(c.class_id, ''),
                'enrollment_year': c.enrollment_year,
                'student_count': student_counts.get(c.class_id, 0),
                'advisor': c.advisor,
                'advisor_name': teacher_name_map.get(c.advisor, c.advisor or ''),
            })
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@class_bp.route('/api/classes', methods=['POST'])
@require_admin
@csrf_protect
def api_create_class():
    data = request.get_json()
    svc = ClassService()
    try:
        svc.create({'class_name': data.get('class_name', ''), 'major_id': data.get('major_id'),
                    'enrollment_year': data.get('enrollment_year'), 'advisor': data.get('advisor', '')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except (ValueError, KeyError) as e:
        return jsonify({'code': 1, 'msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logging.exception('创建班级失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@class_bp.route('/api/classes/<int:class_id>', methods=['GET'])
@require_login
def api_class_detail(class_id):
    svc = ClassService()
    try:
        cls = svc.repo.get_by_id(class_id)
        if not cls:
            return jsonify({'code': 1, 'msg': '班级不存在'})
        # 解析 advisor 为教师姓名
        advisor_name = ''
        if cls.advisor:
            from entity.teacher import Teacher
            teacher = svc.repo.db.query(Teacher.name).filter(Teacher.teacher_id == cls.advisor).first()
            if teacher:
                advisor_name = teacher.name
            else:
                advisor_name = cls.advisor
        return jsonify({'code': 0, 'data': {
            'class_id': cls.class_id,
            'class_name': cls.class_name,
            'major_id': cls.major_id,
            'enrollment_year': cls.enrollment_year,
            'advisor': cls.advisor or '',
            'advisor_name': advisor_name,
        }})
    finally:
        svc.close()


@class_bp.route('/api/classes/<int:class_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_class(class_id):
    data = request.get_json()
    svc = ClassService()
    try:
        # 仅传递请求中存在的字段，避免空字符串覆盖已有数据
        update_data = {k: v for k, v in data.items() if k in ('class_name', 'major_id', 'enrollment_year', 'advisor') and v is not None and v != ''}
        result = svc.update(class_id, update_data)
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '班级不存在'})
    finally:
        svc.close()


@class_bp.route('/api/classes/<int:class_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_class(class_id):
    svc = ClassService()
    try:
        svc.delete(class_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()
