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

    svc = MajorService()
    try:
        if simple == '1':
            if dept_id:
                majors = svc.repo.find_all_by(dept_id=dept_id)
            else:
                majors = svc.get_all()
            return jsonify([{'major_id': m.major_id, 'major_name': m.major_name, 'dept_id': m.dept_id} for m in majors])

        from entity.major import Major
        q = svc.repo.db.query(Major)
        if dept_id:
            q = q.filter(Major.dept_id == dept_id)
        if keyword:
            q = q.filter(Major.major_name.like(f'%{escape_like(keyword)}%', escape='\\'))
        q = q.order_by(Major.major_name)
        items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{'major_id': m.major_id, 'major_name': m.major_name, 'dept_id': m.dept_id, 'duration': m.duration} for m in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@major_bp.route('/api/majors', methods=['POST'])
@require_admin
@csrf_protect
def api_create_major():
    data = request.get_json()
    svc = MajorService()
    try:
        svc.create({'major_name': data.get('major_name', ''), 'dept_id': data.get('dept_id'), 'duration': data.get('duration', 4)})
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
        result = svc.update(major_id, {'major_name': data.get('major_name', ''), 'dept_id': data.get('dept_id'), 'duration': data.get('duration', 4)})
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
