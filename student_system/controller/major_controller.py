"""专业管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.major_service import MajorService
from repository.base import escape_like
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

major_bp = Blueprint('major', __name__)


@major_bp.route('/majors')
def majors_page():
    return render_template('majors.html')


@major_bp.route('/api/majors', methods=['GET'])
def api_majors():
    dept_id = request.args.get('dept_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    simple = request.args.get('simple', '')
    filters_json = request.args.get('filters', '')

    svc = MajorService()
    try:
        if simple == '1':
            if dept_id:
                majors = svc.repo.find_all_by(dept_id=dept_id)
            else:
                majors = svc.get_all()
            return jsonify([{'major_id': m.major_id, 'major_name': m.major_name, 'dept_id': m.dept_id} for m in majors])

        from entity.major import Major
        from entity.department import Department
        from sqlalchemy.orm import joinedload

        SORT_FIELDS = {
            'major_name': Major.major_name,
            'dept_id': Major.dept_id,
            'duration': Major.duration,
            'degree_type': Major.degree_type,
            'major_id': Major.major_id,
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
            order_by = order_col if order_col is not None else Major.major_name
            items, total = svc.repo.filter_paginate(filters, page, page_size, order_by)
        else:
            q = svc.repo.db.query(Major).options(joinedload(Major.department))
            if dept_id:
                q = q.filter(Major.dept_id == dept_id)
            if keyword:
                q = q.filter(Major.major_name.like(f'%{escape_like(keyword)}%', escape='\\'))
            if order_col is not None:
                q = q.order_by(order_col)
            else:
                q = q.order_by(Major.major_name)
            items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{'major_id': m.major_id, 'major_name': m.major_name, 'dept_id': m.dept_id,
                 'duration': m.duration, 'degree_type': m.degree_type or '',
                 'description': m.description or '',
                 'dept_name': m.department.dept_name if m.department else ''} for m in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@major_bp.route('/api/majors/<int:major_id>', methods=['GET'])
@require_login
def api_major_detail(major_id):
    svc = MajorService()
    try:
        from entity.major import Major
        from entity.department import Department
        from sqlalchemy.orm import joinedload
        major = svc.repo.db.query(Major).options(joinedload(Major.department)).filter(Major.major_id == major_id).first()
        if not major:
            return jsonify({'code': 1, 'msg': '专业不存在'})
        return jsonify({'code': 0, 'data': {
            'major_id': major.major_id,
            'major_name': major.major_name,
            'dept_id': major.dept_id,
            'duration': major.duration,
            'degree_type': major.degree_type or '',
            'description': major.description or '',
            'dept_name': major.department.dept_name if major.department else '',
        }})
    finally:
        svc.close()


@major_bp.route('/api/majors', methods=['POST'])
@require_admin
@csrf_protect
def api_create_major():
    data = request.get_json()
    svc = MajorService()
    try:
        svc.create({'major_name': data.get('major_name', ''), 'dept_id': data.get('dept_id'),
                    'duration': data.get('duration', 4), 'degree_type': data.get('degree_type', '学士'),
                    'description': data.get('description', '')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except (ValueError, KeyError) as e:
        return jsonify({'code': 1, 'msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logging.exception('创建专业失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@major_bp.route('/api/majors/<int:major_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_major(major_id):
    data = request.get_json()
    svc = MajorService()
    try:
        # 仅传递请求中存在的字段，避免空字符串覆盖已有数据
        update_data = {k: v for k, v in data.items() if k in ('major_name', 'dept_id', 'duration', 'degree_type', 'description') and v is not None and v != ''}
        result = svc.update(major_id, update_data)
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '专业不存在'})
    finally:
        svc.close()


@major_bp.route('/api/majors/<int:major_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_major(major_id):
    svc = MajorService()
    try:
        svc.delete(major_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()
