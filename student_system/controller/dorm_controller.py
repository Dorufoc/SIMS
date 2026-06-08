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

    svc = DormService()
    try:
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
                 'capacity': r.capacity, 'occupied': r.occupied} for r in rooms]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


# ---- 住宿分配 ----
@dorm_bp.route('/api/dorm_assignments', methods=['GET'])
@require_login
def api_dorm_assignments():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    svc = DormService()
    try:
        items, total = svc.get_assignments(page, page_size)
        total_pages = (total + page_size - 1) // page_size
        data = [{'assign_id': a.assign_id, 'student_id': a.student_id, 'room_id': a.room_id,
                 'bed_number': a.bed_number, 'check_in_date': str(a.check_in_date),
                 'check_out_date': str(a.check_out_date) if a.check_out_date else None,
                 'status': a.status, 'remark': a.remark} for a in items]
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
