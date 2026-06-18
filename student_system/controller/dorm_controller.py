"""宿舍管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.dorm_service import DormService
from middleware.auth_middleware import require_login, csrf_protect
import logging

dorm_bp = Blueprint('dorm', __name__)


@dorm_bp.route('/dorm_rooms')
def dorm_rooms_page():
    return render_template('dorm_rooms.html')


@dorm_bp.route('/dorm_assignments')
def dorm_assignments_page():
    return render_template('dorm_assignments.html')


# ---- 房间管理 ----
@dorm_bp.route('/api/dorm_rooms', methods=['GET'])
@require_login
def api_dorm_rooms():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')

    svc = DormService()
    try:
        from entity.dorm_room import DormRoom

        SORT_FIELDS = {
            'room_id': DormRoom.room_id,
            'building': DormRoom.building,
            'room_number': DormRoom.room_number,
            'capacity': DormRoom.capacity,
            'occupied': DormRoom.occupied,
            'gender_limit': DormRoom.gender_limit,
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
            order_by = order_col if order_col is not None else svc.room_repo.model.room_id
            items, total = svc.room_repo.filter_paginate(filters, page, page_size, order_by)
        else:
            if order_col is not None:
                q = svc.room_repo.db.query(DormRoom)
                q = q.order_by(order_col)
                items, total = svc.room_repo.paginate(page, page_size, q)
            else:
                items, total = svc.get_rooms(page, page_size)
        total_pages = (total + page_size - 1) // page_size
        data = [{'room_id': d.room_id, 'building': d.building, 'room_number': d.room_number,
                 'capacity': d.capacity, 'occupied': d.occupied, 'gender_limit': d.gender_limit,
                 'phone': d.phone} for d in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_rooms', methods=['POST'])
@require_login
@csrf_protect
def api_create_dorm_room():
    data = request.get_json()
    svc = DormService()
    try:
        svc.create_room({'building': data.get('building', ''), 'room_number': data.get('room_number', ''),
                         'capacity': data.get('capacity', 4), 'gender_limit': data.get('gender_limit', '不限'),
                         'phone': data.get('phone', '')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except Exception as e:
        logging.exception('创建宿舍房间失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_rooms/<int:room_id>', methods=['GET'])
@require_login
def api_dorm_room_detail(room_id):
    svc = DormService()
    try:
        room = svc.room_repo.get_by_id(room_id)
        if not room:
            return jsonify({'code': 1, 'msg': '房间不存在'})
        return jsonify({'code': 0, 'data': {
            'room_id': room.room_id, 'building': room.building,
            'room_number': room.room_number, 'capacity': room.capacity,
            'occupied': room.occupied, 'gender_limit': room.gender_limit,
            'phone': room.phone or '',
        }})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_rooms/<int:room_id>', methods=['PUT'])
@require_login
@csrf_protect
def api_update_dorm_room(room_id):
    data = request.get_json()
    svc = DormService()
    try:
        result = svc.update_room(room_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '房间不存在'})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_rooms/<int:room_id>', methods=['DELETE'])
@require_login
@csrf_protect
def api_delete_dorm_room(room_id):
    svc = DormService()
    try:
        existing = svc.room_repo.get_by_id(room_id)
        if not existing:
            return jsonify({'code': 1, 'msg': '宿舍房间不存在'}), 404
        svc.delete_room(room_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_buildings', methods=['GET'])
@require_login
def api_dorm_buildings():
    svc = DormService()
    try:
        buildings = svc.get_buildings()
        return jsonify({'code': 0, 'data': buildings})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_rooms/available', methods=['GET'])
@require_login
def api_available_rooms():
    svc = DormService()
    try:
        rooms = svc.get_available_rooms()
        data = [{'room_id': r.room_id, 'building': r.building, 'room_number': r.room_number,
                 'capacity': r.capacity, 'occupied': r.occupied,
                 'gender_limit': r.gender_limit,
                 'available_beds': (r.capacity or 0) - (r.occupied or 0)} for r in rooms]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


# ---- 住宿分配 ----
@dorm_bp.route('/api/dorm_assignments', methods=['GET'])
@require_login
def api_dorm_assignments():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')

    svc = DormService()
    try:
        from entity.student import Student
        from entity.dorm_room import DormRoom
        from entity.dorm_assignment import DormAssignment
        from repository.base import escape_like

        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []

            q = svc.assignment_repo.db.query(DormAssignment)

            # 直接字段映射（DormAssignment 本表字段）
            DIRECT_FIELD_MAP = {
                'student_id': DormAssignment.student_id,
                'bed_number': DormAssignment.bed_number,
                'status': DormAssignment.status,
                'check_in_date': DormAssignment.check_in_date,
            }
            # 跨表字段映射：{field: (related_model, fk_column, target_column)}
            CROSS_FIELD_MAP = {
                'student_name': (DormAssignment.student_id, Student.student_id, Student.name),
                'gender': (DormAssignment.student_id, Student.student_id, Student.gender),
                'building': (DormAssignment.room_id, DormRoom.room_id, DormRoom.building),
                'room_number': (DormAssignment.room_id, DormRoom.room_id, DormRoom.room_number),
            }

            for f in filters:
                field = f.get('field', '')
                op = f.get('op', 'eq')
                value = f.get('value', '')

                if not field:
                    continue

                # 处理直接字段
                if field in DIRECT_FIELD_MAP:
                    column = DIRECT_FIELD_MAP[field]

                    # 日期列使用字符串运算符时自动转型
                    from sqlalchemy import Date as SA_Date
                    if isinstance(column.type, SA_Date) and op in ('contains', 'startswith', 'endswith'):
                        from sqlalchemy import cast, String as SA_String
                        column = cast(column, SA_String)

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

                # 处理跨表字段（使用子查询）
                elif field in CROSS_FIELD_MAP:
                    fk_col, pk_col, target_col = CROSS_FIELD_MAP[field]

                    if op == 'eq':
                        subq = svc.assignment_repo.db.query(pk_col).filter(target_col == value)
                    elif op == 'neq':
                        subq = svc.assignment_repo.db.query(pk_col).filter(target_col != value)
                    elif op == 'contains':
                        subq = svc.assignment_repo.db.query(pk_col).filter(
                            target_col.like(f'%{escape_like(value)}%', escape='\\'))
                    elif op == 'startswith':
                        subq = svc.assignment_repo.db.query(pk_col).filter(
                            target_col.like(f'{escape_like(value)}%', escape='\\'))
                    elif op == 'endswith':
                        subq = svc.assignment_repo.db.query(pk_col).filter(
                            target_col.like(f'%{escape_like(value)}', escape='\\'))
                    else:
                        continue

                    q = q.filter(fk_col.in_(subq))

            q = q.order_by(DormAssignment.assign_id.desc())
            items, total = svc.assignment_repo.paginate(page, page_size, q)
        else:
            items, total = svc.get_assignments(page, page_size)

        total_pages = (total + page_size - 1) // page_size
        data = []
        for a in items:
            student = a.student
            room = a.room
            gender_val = student.gender if student else ''
            data.append({
                'assign_id': a.assign_id, 'student_id': a.student_id,
                'student_name': student.name if student else '',
                'gender': gender_val,
                'gender_text': '男' if gender_val == 'M' else ('女' if gender_val == 'F' else ''),
                'building': room.building if room else '',
                'room_number': room.room_number if room else '',
                'room_id': a.room_id, 'bed_number': a.bed_number,
                'check_in_date': str(a.check_in_date),
                'check_out_date': str(a.check_out_date) if a.check_out_date else None,
                'status': a.status, 'remark': a.remark,
            })
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_assignments', methods=['POST'])
@require_login
@csrf_protect
def api_assign_dorm():
    data = request.get_json()
    svc = DormService()
    try:
        success, msg = svc.assign(data)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@dorm_bp.route('/api/dorm_assignments/<int:assign_id>/checkout', methods=['POST'])
@require_login
@csrf_protect
def api_checkout(assign_id):
    svc = DormService()
    try:
        success, msg = svc.checkout(assign_id)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()
