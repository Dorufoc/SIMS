"""
基础数据管理API模块
提供院系、专业、班级、教师的增删改查接口
"""

import json

import pymysql
from flask import Blueprint, jsonify, request

from db_utils import build_filter_sql, execute, get_page_data, query

api_basic = Blueprint('api_basic', __name__)


# ============================================
# 院系管理API
# ============================================

@api_basic.route('/api/departments', methods=['GET'])
def get_departments():
    """获取院系列表，支持分页和搜索"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    filters_json = request.args.get('filters', '')

    base_sql = "SELECT * FROM departments WHERE 1=1"
    params = []

    if filters_json:
        try:
            filters = json.loads(filters_json)
            filter_clause, filter_params = build_filter_sql(filters, {
                'dept_id': 'dept_id',
                'dept_name': 'dept_name',
                'dean': 'dean',
                'phone': 'phone'
            })
            base_sql += " " + filter_clause
            params.extend(filter_params)
        except (json.JSONDecodeError, TypeError):
            pass

    if keyword:
        base_sql += " AND dept_name LIKE %s"
        params.append(f"%{keyword}%")

    if page > 0:
        base_sql += " ORDER BY dept_id"
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        base_sql += " ORDER BY dept_name"
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_basic.route('/api/departments', methods=['POST'])
def create_department():
    """新增院系"""
    data = request.get_json()
    dept_name = data.get('dept_name', '').strip()
    dean = data.get('dean', '').strip()
    phone = data.get('phone', '').strip()

    if not dept_name:
        return jsonify({'code': 1, 'msg': '院系名称不能为空'})

    try:
        execute(
            "INSERT INTO departments(dept_name, dean, phone) VALUES(%s, %s, %s)",
            (dept_name, dean or None, phone or None)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '院系名称已存在'})


@api_basic.route('/api/departments/<int:dept_id>', methods=['PUT'])
def update_department(dept_id):
    """更新院系信息"""
    data = request.get_json()
    dept_name = data.get('dept_name', '').strip()
    dean = data.get('dean', '').strip()
    phone = data.get('phone', '').strip()

    if not dept_name:
        return jsonify({'code': 1, 'msg': '院系名称不能为空'})

    try:
        execute(
            "UPDATE departments SET dept_name=%s, dean=%s, phone=%s WHERE dept_id=%s",
            (dept_name, dean or None, phone or None, dept_id)
        )
        return jsonify({'code': 0, 'msg': '更新成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '院系名称已存在'})


@api_basic.route('/api/departments/<int:dept_id>', methods=['DELETE'])
def delete_department(dept_id):
    """删除院系（检查关联）"""
    # 检查是否有专业关联
    count = query("SELECT COUNT(*) AS cnt FROM majors WHERE dept_id = %s", (dept_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该院系下存在专业，无法删除'})

    execute("DELETE FROM departments WHERE dept_id = %s", (dept_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


# ============================================
# 专业管理API
# ============================================

@api_basic.route('/api/majors', methods=['GET'])
def get_majors():
    """获取专业列表，支持按院系筛选、分页和搜索"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    dept_id = request.args.get('dept_id', type=int)
    keyword = request.args.get('keyword', '').strip()
    filters_json = request.args.get('filters', '')

    base_sql = """
        SELECT m.*, d.dept_name
        FROM majors m
        LEFT JOIN departments d ON m.dept_id = d.dept_id
        WHERE 1=1
    """
    params = []

    if filters_json:
        try:
            filters = json.loads(filters_json)
            filter_clause, filter_params = build_filter_sql(filters, {
                'major_id': 'm.major_id',
                'major_name': 'm.major_name',
                'dept_name': 'd.dept_name',
                'duration': 'm.duration',
                'degree_type': 'm.degree_type'
            })
            base_sql += " " + filter_clause
            params.extend(filter_params)
        except (json.JSONDecodeError, TypeError):
            pass

    if dept_id:
        base_sql += " AND m.dept_id = %s"
        params.append(dept_id)

    if keyword:
        base_sql += " AND m.major_name LIKE %s"
        params.append(f"%{keyword}%")

    base_sql += " ORDER BY m.major_id"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_basic.route('/api/majors', methods=['POST'])
def create_major():
    """新增专业"""
    data = request.get_json()
    major_name = data.get('major_name', '').strip()
    dept_id = data.get('dept_id', type=int)
    duration = data.get('duration', 4)

    if not major_name:
        return jsonify({'code': 1, 'msg': '专业名称不能为空'})

    if not dept_id:
        return jsonify({'code': 1, 'msg': '请选择所属院系'})

    try:
        execute(
            "INSERT INTO majors(major_name, dept_id, duration) VALUES(%s, %s, %s)",
            (major_name, dept_id, duration)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError as e:
        return jsonify({'code': 1, 'msg': f'新增失败：{str(e)}'})


@api_basic.route('/api/majors/<int:major_id>', methods=['PUT'])
def update_major(major_id):
    """更新专业信息"""
    data = request.get_json()
    major_name = data.get('major_name', '').strip()
    dept_id = data.get('dept_id', type=int)
    duration = data.get('duration', 4)

    if not major_name:
        return jsonify({'code': 1, 'msg': '专业名称不能为空'})

    if not dept_id:
        return jsonify({'code': 1, 'msg': '请选择所属院系'})

    execute(
        "UPDATE majors SET major_name=%s, dept_id=%s, duration=%s WHERE major_id=%s",
        (major_name, dept_id, duration, major_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_basic.route('/api/majors/<int:major_id>', methods=['DELETE'])
def delete_major(major_id):
    """删除专业（检查关联）"""
    # 检查是否有班级关联
    count = query("SELECT COUNT(*) AS cnt FROM classes WHERE major_id = %s", (major_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该专业下存在班级，无法删除'})

    # 检查是否有培养计划关联
    count = query("SELECT COUNT(*) AS cnt FROM curriculum WHERE major_id = %s", (major_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该专业已设置培养计划，无法删除'})

    execute("DELETE FROM majors WHERE major_id = %s", (major_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


# ============================================
# 班级管理API
# ============================================

@api_basic.route('/api/classes', methods=['GET'])
def get_classes():
    """获取班级列表，支持按专业筛选、分页和搜索"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    major_id = request.args.get('major_id', type=int)
    dept_id = request.args.get('dept_id', type=int)
    enrollment_year = request.args.get('enrollment_year', type=int)
    keyword = request.args.get('keyword', '').strip()
    filters_json = request.args.get('filters', '')

    base_sql = """
        SELECT c.*, m.major_name, d.dept_name
        FROM classes c
        LEFT JOIN majors m ON c.major_id = m.major_id
        LEFT JOIN departments d ON m.dept_id = d.dept_id
        WHERE 1=1
    """
    params = []

    if filters_json:
        try:
            filters = json.loads(filters_json)
            filter_clause, filter_params = build_filter_sql(filters, {
                'class_id': 'c.class_id',
                'class_name': 'c.class_name',
                'major_name': 'm.major_name',
                'dept_name': 'd.dept_name',
                'enrollment_year': 'c.enrollment_year',
                'student_count': 'c.student_count',
                'counselor': 'c.counselor'
            })
            base_sql += " " + filter_clause
            params.extend(filter_params)
        except (json.JSONDecodeError, TypeError):
            pass

    if major_id:
        base_sql += " AND c.major_id = %s"
        params.append(major_id)

    if dept_id:
        base_sql += " AND m.dept_id = %s"
        params.append(dept_id)

    if enrollment_year:
        base_sql += " AND c.enrollment_year = %s"
        params.append(enrollment_year)

    if keyword:
        base_sql += " AND c.class_name LIKE %s"
        params.append(f"%{keyword}%")

    base_sql += " ORDER BY c.enrollment_year DESC, c.class_id"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_basic.route('/api/classes', methods=['POST'])
def create_class():
    """新增班级"""
    data = request.get_json()
    class_name = data.get('class_name', '').strip()
    major_id = data.get('major_id', type=int)
    enrollment_year = data.get('enrollment_year', type=int)
    advisor = data.get('advisor', '').strip()

    if not class_name:
        return jsonify({'code': 1, 'msg': '班级名称不能为空'})

    if not major_id:
        return jsonify({'code': 1, 'msg': '请选择所属专业'})

    if not enrollment_year:
        return jsonify({'code': 1, 'msg': '请输入入学年份'})

    try:
        execute(
            "INSERT INTO classes(class_name, major_id, enrollment_year, advisor) VALUES(%s, %s, %s, %s)",
            (class_name, major_id, enrollment_year, advisor or None)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError as e:
        return jsonify({'code': 1, 'msg': f'新增失败：{str(e)}'})


@api_basic.route('/api/classes/<int:class_id>', methods=['PUT'])
def update_class(class_id):
    """更新班级信息"""
    data = request.get_json()
    class_name = data.get('class_name', '').strip()
    major_id = data.get('major_id', type=int)
    enrollment_year = data.get('enrollment_year', type=int)
    advisor = data.get('advisor', '').strip()

    if not class_name:
        return jsonify({'code': 1, 'msg': '班级名称不能为空'})

    if not major_id:
        return jsonify({'code': 1, 'msg': '请选择所属专业'})

    if not enrollment_year:
        return jsonify({'code': 1, 'msg': '请输入入学年份'})

    execute(
        "UPDATE classes SET class_name=%s, major_id=%s, enrollment_year=%s, advisor=%s WHERE class_id=%s",
        (class_name, major_id, enrollment_year, advisor or None, class_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_basic.route('/api/classes/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    """删除班级（检查关联）"""
    # 检查是否有学生关联
    count = query("SELECT COUNT(*) AS cnt FROM students WHERE class_id = %s", (class_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该班级下存在学生，无法删除'})

    execute("DELETE FROM classes WHERE class_id = %s", (class_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


# ============================================
# 教师管理API
# ============================================

@api_basic.route('/api/teachers', methods=['GET'])
def get_teachers():
    """获取教师列表，支持按院系筛选、分页和搜索"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    dept_id = request.args.get('dept_id', type=int)
    keyword = request.args.get('keyword', '').strip()
    filters_json = request.args.get('filters', '')

    base_sql = """
        SELECT t.*, d.dept_name
        FROM teachers t
        LEFT JOIN departments d ON t.dept_id = d.dept_id
        WHERE 1=1
    """
    params = []

    if filters_json:
        try:
            filters = json.loads(filters_json)
            filter_clause, filter_params = build_filter_sql(filters, {
                'teacher_id': 't.teacher_id',
                'name': 't.name',
                'gender': "CASE WHEN t.gender = 'M' THEN '男' WHEN t.gender = 'F' THEN '女' ELSE '' END",
                'dept_name': 'd.dept_name',
                'title': 't.title',
                'phone': 't.phone'
            })
            base_sql += " " + filter_clause
            params.extend(filter_params)
        except (json.JSONDecodeError, TypeError):
            pass

    if dept_id:
        base_sql += " AND t.dept_id = %s"
        params.append(dept_id)

    if keyword:
        base_sql += " AND (t.name LIKE %s OR t.teacher_id LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    base_sql += " ORDER BY t.teacher_id"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_basic.route('/api/teachers/<teacher_id>', methods=['GET'])
def get_teacher(teacher_id):
    """获取单个教师详情"""
    rows = query(
        """SELECT t.*, d.dept_name
           FROM teachers t
           LEFT JOIN departments d ON t.dept_id = d.dept_id
           WHERE t.teacher_id = %s""",
        (teacher_id,)
    )
    if rows:
        return jsonify({'code': 0, 'data': rows[0]})
    return jsonify({'code': 1, 'msg': '教师不存在'})


@api_basic.route('/api/teachers', methods=['POST'])
def create_teacher():
    """新增教师"""
    data = request.get_json()
    teacher_id = data.get('teacher_id', '').strip()
    name = data.get('name', '').strip()
    gender = data.get('gender', '').strip()
    title = data.get('title', '').strip()
    dept_id = data.get('dept_id', type=int)
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    if not teacher_id:
        return jsonify({'code': 1, 'msg': '教师工号不能为空'})

    if not name:
        return jsonify({'code': 1, 'msg': '教师姓名不能为空'})

    try:
        execute(
            """INSERT INTO teachers(teacher_id, name, gender, title, dept_id, phone, email)
               VALUES(%s, %s, %s, %s, %s, %s, %s)""",
            (teacher_id, name, gender or None, title or None, dept_id or None, phone or None, email or None)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '教师工号已存在'})


@api_basic.route('/api/teachers/<teacher_id>', methods=['PUT'])
def update_teacher(teacher_id):
    """更新教师信息"""
    data = request.get_json()
    name = data.get('name', '').strip()
    gender = data.get('gender', '').strip()
    title = data.get('title', '').strip()
    dept_id = data.get('dept_id', type=int)
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    if not name:
        return jsonify({'code': 1, 'msg': '教师姓名不能为空'})

    execute(
        """UPDATE teachers SET name=%s, gender=%s, title=%s, dept_id=%s, phone=%s, email=%s
           WHERE teacher_id=%s""",
        (name, gender or None, title or None, dept_id or None, phone or None, email or None, teacher_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_basic.route('/api/teachers/<teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    """删除教师（检查关联）"""
    # 检查是否有授课关联
    count = query("SELECT COUNT(*) AS cnt FROM teaching WHERE teacher_id = %s", (teacher_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该教师已有授课安排，无法删除'})

    execute("DELETE FROM teachers WHERE teacher_id = %s", (teacher_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})
