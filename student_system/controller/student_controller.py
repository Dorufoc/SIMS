"""学生 CRUD API"""
from flask import Blueprint, request, jsonify, session, render_template, redirect
from service.student_service import StudentService
from middleware.auth_middleware import require_login, csrf_protect
from repository.base import escape_like
import logging

student_bp = Blueprint('student', __name__)


@student_bp.route('/')
def index():
    from config import get_env_dynamic
    show_mock_data = get_env_dynamic('SHOW_MOCK_DATA_BUTTON', 'false').lower() == 'true'
    return render_template('index.html', show_mock_data=show_mock_data)


@student_bp.route('/my')
def my_info():
    role = session.get('user_role')
    ref_id = session.get('user_ref_id')
    return render_template('my_info.html', role=role, user_ref_id=ref_id)


@student_bp.route('/add', methods=['GET', 'POST'])
@require_login
@csrf_protect
def add_student():
    if request.method == 'GET':
        return render_template('add_stu.html')

    svc = StudentService()
    try:
        data = {
            'student_id': request.form.get('student_id', '').strip(),
            'name': request.form.get('name', '').strip(),
            'gender': request.form.get('gender', '').strip() or None,
            'birth_date': request.form.get('birth_date', '').strip() or None,
            'id_card_no': request.form.get('id_card_no', '').strip() or None,
            'enrollment_year': int(request.form['enrollment_year']) if request.form.get('enrollment_year') else None,
            'dept_id': int(request.form['dept_id']) if request.form.get('dept_id') else None,
            'class_id': int(request.form['class_id']) if request.form.get('class_id') else None,
            'phone': request.form.get('phone', '').strip() or None,
            'email': request.form.get('email', '').strip() or None,
            'address': request.form.get('address', '').strip() or None,
            'status': '在校',
        }
        svc.create(data)
        return jsonify({'code': 0, 'msg': '新增成功'})
    except (ValueError, KeyError) as e:
        return jsonify({'code': 1, 'msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logging.exception('新增学生失败')
        return jsonify({'code': 1, 'msg': '新增失败，请稍后重试'})
    finally:
        svc.close()


@student_bp.route('/api/students/<student_id>', methods=['GET'])
@require_login
def api_student_detail(student_id):
    """获取单个学生基本信息"""
    svc = StudentService()
    try:
        student = svc.get_full_info(student_id)
        if not student:
            return jsonify({'code': 1, 'msg': '学生不存在'})
        return jsonify({'code': 0, 'data': {
            'student_id': student.student_id,
            'name': student.name,
            'gender': student.gender,
            'gender_text': '男' if student.gender == 'M' else ('女' if student.gender == 'F' else ''),
            'birth_date': str(student.birth_date) if student.birth_date else None,
            'phone': student.phone,
            'email': student.email,
            'address': student.address,
            'status': student.status,
            'enrollment_year': student.enrollment_year,
            'class_id': student.class_id,
            'class_name': student.class_.class_name if student.class_ else None,
            'major_name': student.class_.major.major_name if student.class_ and student.class_.major else None,
            'dept_name': student.class_.major.department.dept_name if student.class_ and student.class_.major and student.class_.major.department else None,
        }})
    finally:
        svc.close()


@student_bp.route('/api/my/dorm', methods=['GET'])
@require_login
def get_my_dorm():
    """获取当前学生的宿舍分配信息"""
    if session.get('user_role') != 'student':
        return jsonify({'code': 1, 'msg': '仅学生可操作'}), 403

    student_id = session.get('user_ref_id')
    if not student_id:
        return jsonify({'code': 1, 'msg': '未关联学生信息'}), 400

    svc = StudentService()
    try:
        data = svc.get_my_dorm(student_id)
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@student_bp.route('/manage')
def manage():
    page = request.args.get('page', 1, type=int)
    return render_template('manage.html', page=page)


@student_bp.route('/edit/<student_id>', methods=['GET', 'POST'])
@require_login
@csrf_protect
def edit_student(student_id):
    if request.method == 'GET':
        svc = StudentService()
        try:
            student = svc.get_full_info(student_id)
            if student:
                return jsonify({
                    'student_id': student.student_id,
                    'name': student.name,
                    'gender': student.gender,
                    'gender_text': '男' if student.gender == 'M' else ('女' if student.gender == 'F' else ''),
                    'birth_date': str(student.birth_date) if student.birth_date else None,
                    'phone': student.phone,
                    'email': student.email,
                    'address': student.address,
                    'status': student.status,
                    'class_id': student.class_id,
                    'class_name': student.class_.class_name if student.class_ else None,
                    'major_name': student.class_.major.major_name if student.class_ and student.class_.major else None,
                    'dept_name': student.class_.major.department.dept_name if student.class_ and student.class_.major and student.class_.major.department else None,
                })
            return jsonify({})
        finally:
            svc.close()

    svc = StudentService()
    try:
        data = {
            'name': request.form.get('name', '').strip(),
            'gender': request.form.get('gender', '').strip() or None,
            'birth_date': request.form.get('birth_date', '').strip() or None,
            'phone': request.form.get('phone', '').strip() or None,
            'email': request.form.get('email', '').strip() or None,
            'address': request.form.get('address', '').strip() or None,
            'status': request.form.get('status', '在校').strip(),
            'class_id': int(request.form['class_id']) if request.form.get('class_id') else None,
        }
        svc.update(student_id, data)
        return jsonify({'code': 0, 'msg': '修改成功'})
    except (ValueError, KeyError) as e:
        return jsonify({'code': 1, 'msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logging.exception('修改学生失败')
        return jsonify({'code': 1, 'msg': '修改失败，请稍后重试'})
    finally:
        svc.close()


@student_bp.route('/delete/<student_id>', methods=['POST'])
@require_login
@csrf_protect
def delete_student(student_id):
    svc = StudentService()
    try:
        svc.delete(student_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()


@student_bp.route('/api/students', methods=['GET'])
@require_login
def api_students_list():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    filters_json = request.args.get('filters', '')

    svc = StudentService()
    try:
        from entity.student import Student
        from entity.class_ import Class
        from entity.major import Major
        from entity.department import Department
        from sqlalchemy.orm import joinedload

        SORT_FIELDS = {
            'student_id': Student.student_id,
            'student_name': Student.name,
            'gender': Student.gender,
            'birth_date': Student.birth_date,
            'enrollment_year': Student.enrollment_year,
            'status': Student.status,
            'phone': Student.phone,
            'email': Student.email,
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
            items, total = svc.repo.filter_paginate(filters, page, page_size, order_col)
        else:
            q = svc.repo.db.query(Student).options(
                joinedload(Student.class_).joinedload(Class.major).joinedload(Major.department)
            )
            if keyword:
                escaped = escape_like(keyword)
                q = q.filter(
                    (Student.student_id.like(f'%{escaped}%', escape='\\')) |
                    (Student.name.like(f'%{escaped}%', escape='\\')) |
                    (Student.phone.like(f'%{escaped}%', escape='\\'))
                )
            if order_col is not None:
                q = q.order_by(order_col)
            else:
                q = q.order_by(Student.student_id)
            items, total = svc.repo.paginate(page, page_size, q)
        data = []
        for s in items:
            data.append({
                'student_id': s.student_id,
                'name': s.name,
                'student_name': s.name,  # 前端 manage.html 使用 student_name
                'gender': s.gender or '',
                'gender_text': '男' if s.gender == 'M' else ('女' if s.gender == 'F' else ''),
                'birth_date': str(s.birth_date) if s.birth_date else '',
                'enrollment_year': s.enrollment_year,
                'status': s.status,
                'phone': s.phone or '',
                'email': s.email or '',
                'class_id': s.class_id,
                'class_name': s.class_.class_name if s.class_ else '',
                'major_name': s.class_.major.major_name if s.class_ and s.class_.major else '',
                'dept_name': s.class_.major.department.dept_name if s.class_ and s.class_.major and s.class_.major.department else '',
            })
        total_pages = (total + page_size - 1) // page_size
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@student_bp.route('/api/my/profile/student', methods=['POST'])
@require_login
@csrf_protect
def update_my_student_profile():
    if session.get('user_role') != 'student':
        return jsonify({'code': 1, 'msg': '仅学生可操作'}), 403

    student_id = session.get('user_ref_id')
    if not student_id:
        return jsonify({'code': 1, 'msg': '未关联学生信息'}), 400

    svc = StudentService()
    try:
        data = {
            'phone': request.form.get('phone', '').strip() or None,
            'email': request.form.get('email', '').strip() or None,
            'address': request.form.get('address', '').strip() or None,
        }
        svc.update(student_id, data)
        return jsonify({'code': 0, 'msg': '修改成功'})
    finally:
        svc.close()
