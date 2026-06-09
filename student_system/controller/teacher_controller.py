"""教师管理 API"""
from flask import Blueprint, request, jsonify, render_template, session
from service.teacher_service import TeacherService
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

teacher_bp = Blueprint('teacher', __name__)


@teacher_bp.route('/teachers')
def teachers_page():
    return render_template('teachers.html')


@teacher_bp.route('/api/teachers', methods=['GET'])
@require_login
def api_teachers():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()

    svc = TeacherService()
    try:
        from entity.teacher import Teacher
        q = svc.repo.db.query(Teacher)
        if keyword:
            q = q.filter(
                (Teacher.teacher_id.like(f'%{escape_like(keyword)}%', escape='\\')) |
                (Teacher.name.like(f'%{escape_like(keyword)}%', escape='\\'))
            )
        q = q.order_by(Teacher.teacher_id)
        items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{'teacher_id': t.teacher_id, 'name': t.name, 'gender': t.gender,
                 'title': t.title, 'dept_id': t.dept_id, 'phone': t.phone or '', 'email': t.email or ''} for t in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@teacher_bp.route('/api/teachers/<teacher_id>', methods=['GET'])
@require_login
def api_teacher_detail(teacher_id):
    svc = TeacherService()
    try:
        t = svc.get_by_id(teacher_id)
        if not t:
            return jsonify({'code': 1, 'msg': '教师不存在'})
        return jsonify({'code': 0, 'data': {'teacher_id': t.teacher_id, 'name': t.name, 'gender': t.gender,
                        'title': t.title, 'dept_id': t.dept_id, 'phone': t.phone or '', 'email': t.email or ''}})
    finally:
        svc.close()


@teacher_bp.route('/api/teachers', methods=['POST'])
@require_admin
@csrf_protect
def api_create_teacher():
    data = request.get_json()
    svc = TeacherService()
    try:
        svc.create({'teacher_id': data.get('teacher_id', ''), 'name': data.get('name', ''),
                    'gender': data.get('gender'), 'title': data.get('title', ''),
                    'dept_id': data.get('dept_id'), 'phone': data.get('phone', ''), 'email': data.get('email', '')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except (ValueError, KeyError) as e:
        return jsonify({'code': 1, 'msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logging.exception('创建教师失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@teacher_bp.route('/api/teachers/<teacher_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_teacher(teacher_id):
    data = request.get_json()
    svc = TeacherService()
    try:
        result = svc.update(teacher_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '教师不存在'})
    finally:
        svc.close()


@teacher_bp.route('/api/teachers/<teacher_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_teacher(teacher_id):
    svc = TeacherService()
    try:
        svc.delete(teacher_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()


@teacher_bp.route('/api/my/profile/teacher', methods=['POST'])
@csrf_protect
def update_my_teacher_profile():
    if session.get('user_role') != 'teacher':
        return jsonify({'code': 1, 'msg': '仅教师可操作'}), 403

    teacher_id = session.get('user_ref_id')
    if not teacher_id:
        return jsonify({'code': 1, 'msg': '未关联教师信息'}), 400

    svc = TeacherService()
    try:
        svc.update(teacher_id, {'phone': request.form.get('phone', '').strip() or None,
                                'email': request.form.get('email', '').strip() or None})
        return jsonify({'code': 0, 'msg': '修改成功'})
    finally:
        svc.close()
