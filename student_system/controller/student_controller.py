"""学生 CRUD API"""
from flask import Blueprint, request, jsonify, session, render_template, redirect
from service.student_service import StudentService
from middleware.auth_middleware import require_login, csrf_protect
import logging

student_bp = Blueprint('student', __name__)


@student_bp.route('/')
def index():
    return render_template('index.html')


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


@student_bp.route('/manage')
def manage():
    page = request.args.get('page', 1, type=int)
    return render_template('manage.html', page=page)


@student_bp.route('/edit/<student_id>', methods=['GET', 'POST'])
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
def delete_student(student_id):
    svc = StudentService()
    try:
        svc.delete(student_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()


@student_bp.route('/api/students', methods=['GET'])
def api_students_list():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()

    svc = StudentService()
    try:
        items, total = svc.get_list(page, page_size, keyword=keyword)
        data = []
        for s in items:
            data.append({
                'student_id': s.student_id,
                'name': s.name,
                'student_name': s.name,  # 前端 manage.html 使用 student_name
                'gender': '男' if s.gender == 'M' else ('女' if s.gender == 'F' else ''),
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
