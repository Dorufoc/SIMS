"""学期管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.semester_service import SemesterService
from middleware.auth_middleware import require_login, csrf_protect
import logging

semester_bp = Blueprint('semester', __name__)


@semester_bp.route('/semesters')
def semesters_page():
    return render_template('semesters.html')


@semester_bp.route('/api/semesters', methods=['GET'])
@require_login
def api_semesters():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')

    svc = SemesterService()
    try:
        from entity.semester import Semester
        from repository.base import escape_like

        SORT_FIELDS = {
            'semester_id': Semester.semester_id,
            'academic_year': Semester.academic_year,
            'semester_name': Semester.semester_name,
            'is_current': Semester.is_current,
        }
        sort_by = request.args.get('sort_by', '')
        sort_order = request.args.get('sort_order', '')
        order_col = SORT_FIELDS.get(sort_by)
        if order_col is not None:
            if sort_order == 'desc':
                order_col = order_col.desc()

        q = svc.repo.db.query(Semester)

        # 处理筛选条件
        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []

            FIELD_MAP = getattr(svc.repo, 'field_map', {})
            for f in filters:
                field = f.get('field', '')
                op = f.get('op', 'eq')
                value = f.get('value', '')
                if not field:
                    continue
                if FIELD_MAP and field not in FIELD_MAP:
                    continue
                col_name = FIELD_MAP.get(field, field)
                column = getattr(Semester, col_name, None)
                if column is None:
                    continue

                if op == 'eq':
                    # is_current 是布尔类型，需要特殊处理
                    if column.type.python_type == bool:
                        val = value
                        if isinstance(val, str):
                            val = val.lower() in ('true', '1', 'yes')
                        q = q.filter(column == bool(val))
                    else:
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

        if order_col is not None:
            q = q.order_by(order_col)
        else:
            q = q.order_by(Semester.academic_year.desc())

        items, total = svc.repo.paginate(page, page_size, q)
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


@semester_bp.route('/api/semesters/<int:semester_id>', methods=['GET'])
@require_login
def api_get_semester(semester_id):
    svc = SemesterService()
    try:
        s = svc.get_by_id(semester_id)
        if not s:
            return jsonify({'code': 1, 'msg': '学期不存在'})
        data = {'semester_id': s.semester_id, 'academic_year': s.academic_year,
                'semester_name': s.semester_name, 'start_date': str(s.start_date),
                'end_date': str(s.end_date), 'is_current': s.is_current}
        return jsonify({'code': 0, 'data': data})
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
        existing = svc.get_by_id(semester_id)
        if not existing:
            return jsonify({'code': 1, 'msg': '学期不存在'}), 404
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
