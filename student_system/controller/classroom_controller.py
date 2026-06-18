"""教室管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.classroom_service import ClassroomService
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

classroom_bp = Blueprint('classroom', __name__)


@classroom_bp.route('/classrooms')
@require_login
def classrooms_page():
    return render_template('classrooms.html')


@classroom_bp.route('/api/classrooms', methods=['GET'])
@require_login
def api_classrooms():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    svc = ClassroomService()
    try:
        from entity.classroom import Classroom

        SORT_FIELDS = {
            'classroom_id': Classroom.classroom_id,
            'classroom_name': Classroom.classroom_name,
            'building': Classroom.building,
            'floor': Classroom.floor,
            'capacity': Classroom.capacity,
            'type': Classroom.type,
        }
        sort_by = request.args.get('sort_by', '')
        sort_order = request.args.get('sort_order', '')
        order_col = SORT_FIELDS.get(sort_by)
        if order_col is not None:
            if sort_order == 'desc':
                order_col = order_col.desc()

        filters_json = request.args.get('filters', '')
        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []
            order_by = order_col if order_col is not None else Classroom.classroom_id.desc()
            items, total = svc.repo.filter_paginate(filters, page, page_size, order_by)
        else:
            q = svc.repo.db.query(Classroom)
            if order_col is not None:
                q = q.order_by(order_col)
            else:
                q = q.order_by(Classroom.classroom_id.desc())
            items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{
            'classroom_id': c.classroom_id,
            'classroom_name': c.classroom_name,
            'building': c.building or '',
            'floor': c.floor,
            'capacity': c.capacity,
            'type': c.type or '',
        } for c in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@classroom_bp.route('/api/classrooms', methods=['POST'])
@require_admin
@csrf_protect
def api_create_classroom():
    data = request.get_json()
    svc = ClassroomService()
    try:
        svc.create({'classroom_name': data.get('classroom_name', ''),
                    'building': data.get('building', ''),
                    'floor': data.get('floor'),
                    'capacity': data.get('capacity', 30),
                    'type': data.get('type', '普通教室')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except Exception as e:
        logging.exception('创建教室失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@classroom_bp.route('/api/classrooms/<int:classroom_id>', methods=['GET'])
@require_login
def api_classroom_detail(classroom_id):
    svc = ClassroomService()
    try:
        classroom = svc.repo.get_by_id(classroom_id)
        if not classroom:
            return jsonify({'code': 1, 'msg': '教室不存在'})
        return jsonify({'code': 0, 'data': {
            'classroom_id': classroom.classroom_id,
            'classroom_name': classroom.classroom_name,
            'building': classroom.building or '',
            'floor': classroom.floor,
            'capacity': classroom.capacity,
            'type': classroom.type or '',
        }})
    finally:
        svc.close()


@classroom_bp.route('/api/classrooms/<int:classroom_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_classroom(classroom_id):
    data = request.get_json()
    svc = ClassroomService()
    try:
        result = svc.update(classroom_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '教室不存在'})
    finally:
        svc.close()


@classroom_bp.route('/api/classrooms/<int:classroom_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_classroom(classroom_id):
    svc = ClassroomService()
    try:
        svc.delete(classroom_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()
