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
def api_classes():
    major_id = request.args.get('major_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()

    svc = ClassService()
    try:
        from entity.class_ import Class
        q = svc.repo.db.query(Class)
        if major_id:
            q = q.filter(Class.major_id == major_id)
        if keyword:
            q = q.filter(Class.class_name.like(f'%{escape_like(keyword)}%', escape='\\'))
        q = q.order_by(Class.class_name)
        items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{'class_id': c.class_id, 'class_name': c.class_name, 'major_id': c.major_id,
                 'enrollment_year': c.enrollment_year, 'advisor': c.advisor} for c in items]
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


@class_bp.route('/api/classes/<int:class_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_class(class_id):
    data = request.get_json()
    svc = ClassService()
    try:
        result = svc.update(class_id, {'class_name': data.get('class_name', ''), 'major_id': data.get('major_id'),
                                        'enrollment_year': data.get('enrollment_year'), 'advisor': data.get('advisor', '')})
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
