"""
教学管理API模块
提供课程、学期、授课安排、选课、成绩管理接口
"""

import pymysql
from flask import Blueprint, jsonify, request, session

from db_utils import execute, get_page_data, query

api_teaching = Blueprint('api_teaching', __name__)


# ============================================
# 课程管理API
# ============================================

@api_teaching.route('/api/courses', methods=['GET'])
def get_courses():
    """获取课程列表，支持按院系筛选、分页和搜索"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    dept_id = request.args.get('dept_id', type=int)
    course_type = request.args.get('type', '').strip()
    keyword = request.args.get('keyword', '').strip()

    base_sql = """
        SELECT c.*, d.dept_name
        FROM courses c
        LEFT JOIN departments d ON c.dept_id = d.dept_id
        WHERE 1=1
    """
    params = []

    if dept_id:
        base_sql += " AND c.dept_id = %s"
        params.append(dept_id)

    if course_type:
        base_sql += " AND c.type = %s"
        params.append(course_type)

    if keyword:
        base_sql += " AND (c.course_name LIKE %s OR c.course_id LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    base_sql += " ORDER BY c.course_id"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_teaching.route('/api/courses', methods=['POST'])
def create_course():
    """新增课程"""
    data = request.get_json()
    course_id = data.get('course_id', '').strip()
    course_name = data.get('course_name', '').strip()
    credits = data.get('credits', 0)
    hours = data.get('hours', type=int)
    course_type = data.get('type', '').strip()
    dept_id = data.get('dept_id', type=int)

    if not course_id:
        return jsonify({'code': 1, 'msg': '课程编号不能为空'})

    if not course_name:
        return jsonify({'code': 1, 'msg': '课程名称不能为空'})

    if not course_type:
        return jsonify({'code': 1, 'msg': '请选择课程类型'})

    try:
        execute(
            "INSERT INTO courses(course_id, course_name, credits, hours, type, dept_id) VALUES(%s, %s, %s, %s, %s, %s)",
            (course_id, course_name, credits, hours, course_type, dept_id or None)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '课程编号已存在'})


@api_teaching.route('/api/courses/<course_id>', methods=['PUT'])
def update_course(course_id):
    """更新课程信息"""
    data = request.get_json()
    course_name = data.get('course_name', '').strip()
    credits = data.get('credits', 0)
    hours = data.get('hours', type=int)
    course_type = data.get('type', '').strip()
    dept_id = data.get('dept_id', type=int)

    if not course_name:
        return jsonify({'code': 1, 'msg': '课程名称不能为空'})

    if not course_type:
        return jsonify({'code': 1, 'msg': '请选择课程类型'})

    execute(
        "UPDATE courses SET course_name=%s, credits=%s, hours=%s, type=%s, dept_id=%s WHERE course_id=%s",
        (course_name, credits, hours, course_type, dept_id or None, course_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_teaching.route('/api/courses/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    """删除课程（检查关联）"""
    # 检查是否有授课关联
    count = query("SELECT COUNT(*) AS cnt FROM teaching WHERE course_id = %s", (course_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该课程已有授课安排，无法删除'})

    # 检查是否有培养计划关联
    count = query("SELECT COUNT(*) AS cnt FROM curriculum WHERE course_id = %s", (course_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该课程已加入培养计划，无法删除'})

    execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


# ============================================
# 学期管理API
# ============================================

@api_teaching.route('/api/semesters', methods=['GET'])
def get_semesters():
    """获取学期列表"""
    rows = query("SELECT * FROM semesters ORDER BY academic_year DESC, semester_name")
    return jsonify({'code': 0, 'data': rows})


@api_teaching.route('/api/semesters', methods=['POST'])
def create_semester():
    """新增学期"""
    data = request.get_json()
    academic_year = data.get('academic_year', '').strip()
    semester_name = data.get('semester_name', '').strip()
    start_date = data.get('start_date', '').strip()
    end_date = data.get('end_date', '').strip()

    if not academic_year or not semester_name:
        return jsonify({'code': 1, 'msg': '学年和学期名称不能为空'})

    if not start_date or not end_date:
        return jsonify({'code': 1, 'msg': '请选择起止日期'})

    try:
        execute(
            "INSERT INTO semesters(academic_year, semester_name, start_date, end_date) VALUES(%s, %s, %s, %s)",
            (academic_year, semester_name, start_date, end_date)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '该学期已存在'})


@api_teaching.route('/api/semesters/<int:semester_id>', methods=['PUT'])
def update_semester(semester_id):
    """更新学期信息"""
    data = request.get_json()
    academic_year = data.get('academic_year', '').strip()
    semester_name = data.get('semester_name', '').strip()
    start_date = data.get('start_date', '').strip()
    end_date = data.get('end_date', '').strip()

    if not academic_year or not semester_name:
        return jsonify({'code': 1, 'msg': '学年和学期名称不能为空'})

    if not start_date or not end_date:
        return jsonify({'code': 1, 'msg': '请选择起止日期'})

    try:
        execute(
            "UPDATE semesters SET academic_year=%s, semester_name=%s, start_date=%s, end_date=%s WHERE semester_id=%s",
            (academic_year, semester_name, start_date, end_date, semester_id)
        )
        return jsonify({'code': 0, 'msg': '更新成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '该学期已存在'})


@api_teaching.route('/api/semesters/<int:semester_id>', methods=['DELETE'])
def delete_semester(semester_id):
    """删除学期（检查关联）"""
    # 检查是否有授课关联
    count = query("SELECT COUNT(*) AS cnt FROM teaching WHERE semester_id = %s", (semester_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该学期已有授课安排，无法删除'})

    execute("DELETE FROM semesters WHERE semester_id = %s", (semester_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


@api_teaching.route('/api/semesters/<int:semester_id>/set_current', methods=['POST'])
def set_current_semester(semester_id):
    """设置当前学期"""
    # 先将所有学期设为非当前
    execute("UPDATE semesters SET is_current = FALSE")
    # 设置指定学期为当前
    execute("UPDATE semesters SET is_current = TRUE WHERE semester_id = %s", (semester_id,))
    return jsonify({'code': 0, 'msg': '设置成功'})


# ============================================
# 授课安排API
# ============================================

@api_teaching.route('/api/teaching', methods=['GET'])
def get_teaching():
    """获取授课安排列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    semester_id = request.args.get('semester_id', type=int)
    teacher_id = request.args.get('teacher_id', '').strip()
    course_id = request.args.get('course_id', '').strip()

    base_sql = """
        SELECT t.*, c.course_name, c.credits, c.type as course_type,
               te.name as teacher_name, te.title as teacher_title,
               s.academic_year, s.semester_name, s.is_current
        FROM teaching t
        JOIN courses c ON t.course_id = c.course_id
        JOIN teachers te ON t.teacher_id = te.teacher_id
        JOIN semesters s ON t.semester_id = s.semester_id
        WHERE 1=1
    """
    params = []

    if semester_id:
        base_sql += " AND t.semester_id = %s"
        params.append(semester_id)

    if teacher_id:
        base_sql += " AND t.teacher_id = %s"
        params.append(teacher_id)

    if course_id:
        base_sql += " AND t.course_id = %s"
        params.append(course_id)

    base_sql += " ORDER BY s.academic_year DESC, s.semester_name, t.teaching_id"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_teaching.route('/api/teaching', methods=['POST'])
def create_teaching():
    """新增授课安排"""
    data = request.get_json()
    course_id = data.get('course_id', '').strip()
    teacher_id = data.get('teacher_id', '').strip()
    semester_id = data.get('semester_id', type=int)
    classroom = data.get('classroom', '').strip()
    schedule = data.get('schedule', '').strip()
    capacity = data.get('capacity', 30)

    if not course_id or not teacher_id or not semester_id:
        return jsonify({'code': 1, 'msg': '课程、教师和学期不能为空'})

    try:
        execute(
            """INSERT INTO teaching(course_id, teacher_id, semester_id, classroom, schedule, capacity)
               VALUES(%s, %s, %s, %s, %s, %s)""",
            (course_id, teacher_id, semester_id, classroom or None, schedule or None, capacity)
        )
        return jsonify({'code': 0, 'msg': '安排成功'})
    except pymysql.err.IntegrityError as e:
        return jsonify({'code': 1, 'msg': f'安排失败：{str(e)}'})


@api_teaching.route('/api/teaching/<int:teaching_id>', methods=['PUT'])
def update_teaching(teaching_id):
    """更新授课安排"""
    data = request.get_json()
    teacher_id = data.get('teacher_id', '').strip()
    classroom = data.get('classroom', '').strip()
    schedule = data.get('schedule', '').strip()
    capacity = data.get('capacity', 30)

    if not teacher_id:
        return jsonify({'code': 1, 'msg': '教师不能为空'})

    execute(
        """UPDATE teaching SET teacher_id=%s, classroom=%s, schedule=%s, capacity=%s
           WHERE teaching_id=%s""",
        (teacher_id, classroom or None, schedule or None, capacity, teaching_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_teaching.route('/api/teaching/<int:teaching_id>', methods=['DELETE'])
def delete_teaching(teaching_id):
    """取消授课安排（检查关联）"""
    # 检查是否有学生选课
    count = query("SELECT COUNT(*) AS cnt FROM enrollments WHERE teaching_id = %s", (teaching_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '已有学生选课，无法取消'})

    execute("DELETE FROM teaching WHERE teaching_id = %s", (teaching_id,))
    return jsonify({'code': 0, 'msg': '取消成功'})


@api_teaching.route('/api/teachers/<teacher_id>/teaching', methods=['GET'])
def get_teacher_teaching(teacher_id):
    """获取教师的授课列表"""
    semester_id = request.args.get('semester_id', type=int)

    sql = """
        SELECT t.*, c.course_name, c.credits, c.type as course_type,
               s.academic_year, s.semester_name, s.is_current
        FROM teaching t
        JOIN courses c ON t.course_id = c.course_id
        JOIN semesters s ON t.semester_id = s.semester_id
        WHERE t.teacher_id = %s
    """
    params = [teacher_id]

    if semester_id:
        sql += " AND t.semester_id = %s"
        params.append(semester_id)

    sql += " ORDER BY s.academic_year DESC, s.semester_name"

    rows = query(sql, params)
    return jsonify({'code': 0, 'data': rows})


# ============================================
# 选课管理API
# ============================================

def _get_grade_point(score):
    """根据分数计算绩点"""
    if score is None:
        return None
    if score >= 90:
        return 4.0
    elif score >= 80:
        return 3.0
    elif score >= 70:
        return 2.0
    elif score >= 60:
        return 1.0
    else:
        return 0.0


@api_teaching.route('/api/enrollment/available', methods=['GET'])
def get_available_courses():
    """获取可选课程列表（学生选课用）"""
    student_id = request.args.get('student_id', '').strip()

    # 获取当前学期
    current_semester = query("SELECT semester_id FROM semesters WHERE is_current = TRUE LIMIT 1")
    if not current_semester:
        return jsonify({'code': 1, 'msg': '当前没有进行中的学期'})

    semester_id = current_semester[0]['semester_id']

    # 获取可选课程（当前学期、容量未满、未选过的课程）
    sql = """
        SELECT t.*, c.course_name, c.credits, c.hours, c.type as course_type,
               te.name as teacher_name, te.title as teacher_title,
               (SELECT COUNT(*) FROM enrollments e WHERE e.teaching_id = t.teaching_id AND e.status = '正常') as enrolled_count
        FROM teaching t
        JOIN courses c ON t.course_id = c.course_id
        JOIN teachers te ON t.teacher_id = te.teacher_id
        WHERE t.semester_id = %s
          AND t.capacity > (SELECT COUNT(*) FROM enrollments e WHERE e.teaching_id = t.teaching_id AND e.status = '正常')
          AND NOT EXISTS (
              SELECT 1 FROM enrollments e
              WHERE e.teaching_id = t.teaching_id AND e.student_id = %s AND e.status = '正常'
          )
        ORDER BY c.course_id
    """
    rows = query(sql, (semester_id, student_id))
    return jsonify({'code': 0, 'data': rows})


@api_teaching.route('/api/enrollment', methods=['POST'])
def enroll_course():
    """学生选课"""
    data = request.get_json()
    student_id = data.get('student_id', '').strip()
    teaching_id = data.get('teaching_id', type=int)

    if not student_id or not teaching_id:
        return jsonify({'code': 1, 'msg': '参数错误'})

    # 检查课程容量
    teaching = query("""
        SELECT t.*, (SELECT COUNT(*) FROM enrollments e WHERE e.teaching_id = t.teaching_id AND e.status = '正常') as enrolled_count
        FROM teaching t WHERE t.teaching_id = %s
    """, (teaching_id,))

    if not teaching:
        return jsonify({'code': 1, 'msg': '授课安排不存在'})

    if teaching[0]['enrolled_count'] >= teaching[0]['capacity']:
        return jsonify({'code': 1, 'msg': '课程已满，无法选课'})

    # 检查是否已选
    existing = query(
        "SELECT * FROM enrollments WHERE student_id = %s AND teaching_id = %s AND status = '正常'",
        (student_id, teaching_id)
    )
    if existing:
        return jsonify({'code': 1, 'msg': '已选该课程'})

    try:
        execute(
            "INSERT INTO enrollments(student_id, teaching_id, enroll_time, status) VALUES(%s, %s, NOW(), '正常')",
            (student_id, teaching_id)
        )

        # 记录日志
        execute(
            "INSERT INTO enroll_logs(student_id, teaching_id, operation_type, operator, reason) VALUES(%s, %s, '选课', '系统', '学生自主选课')",
            (student_id, teaching_id)
        )

        return jsonify({'code': 0, 'msg': '选课成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '选课失败，可能已选该课程'})


@api_teaching.route('/api/enrollment/<int:enroll_id>/drop', methods=['POST'])
def drop_course(enroll_id):
    """学生退课"""
    data = request.get_json()
    reason = data.get('reason', '学生自主退课')

    # 获取选课记录
    enrollment = query("SELECT * FROM enrollments WHERE enroll_id = %s", (enroll_id,))
    if not enrollment:
        return jsonify({'code': 1, 'msg': '选课记录不存在'})

    student_id = enrollment[0]['student_id']
    teaching_id = enrollment[0]['teaching_id']

    # 更新选课状态为退课
    execute(
        "UPDATE enrollments SET status = '退课' WHERE enroll_id = %s",
        (enroll_id,)
    )

    # 记录日志
    execute(
        "INSERT INTO enroll_logs(student_id, teaching_id, operation_type, operator, reason) VALUES(%s, %s, '退课', '系统', %s)",
        (student_id, teaching_id, reason)
    )

    return jsonify({'code': 0, 'msg': '退课成功'})


@api_teaching.route('/api/students/<student_id>/enrollment', methods=['GET'])
def get_student_enrollment(student_id):
    """获取学生的选课记录"""
    status = request.args.get('status', '').strip()

    sql = """
        SELECT e.*, c.course_name, c.credits, te.name as teacher_name,
               s.academic_year, s.semester_name, t.classroom, t.schedule
        FROM enrollments e
        JOIN teaching t ON e.teaching_id = t.teaching_id
        JOIN courses c ON t.course_id = c.course_id
        JOIN teachers te ON t.teacher_id = te.teacher_id
        JOIN semesters s ON t.semester_id = s.semester_id
        WHERE e.student_id = %s
    """
    params = [student_id]

    if status:
        sql += " AND e.status = %s"
        params.append(status)

    sql += " ORDER BY s.academic_year DESC, s.semester_name, c.course_id"

    rows = query(sql, params)
    return jsonify({'code': 0, 'data': rows})


# ============================================
# 成绩管理API
# ============================================

@api_teaching.route('/api/teaching/<int:teaching_id>/students', methods=['GET'])
def get_teaching_students(teaching_id):
    """获取授课班级的学生列表（用于成绩录入）"""
    sql = """
        SELECT e.*, s.name as student_name, s.gender, c.class_name
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        LEFT JOIN classes c ON s.class_id = c.class_id
        WHERE e.teaching_id = %s AND e.status = '正常'
        ORDER BY s.student_id
    """
    rows = query(sql, (teaching_id,))
    return jsonify({'code': 0, 'data': rows})


@api_teaching.route('/api/enrollment/<int:enroll_id>/score', methods=['PUT'])
def update_score(enroll_id):
    """录入/修改成绩"""
    data = request.get_json()
    score = data.get('score')
    operator = data.get('operator', '系统')
    reason = data.get('reason', '')

    if score is not None:
        score = float(score)
        if score < 0 or score > 100:
            return jsonify({'code': 1, 'msg': '成绩必须在0-100之间'})

    # 获取原成绩
    old_enrollment = query("SELECT * FROM enrollments WHERE enroll_id = %s", (enroll_id,))
    if not old_enrollment:
        return jsonify({'code': 1, 'msg': '选课记录不存在'})

    old_score = old_enrollment[0]['score']
    student_id = old_enrollment[0]['student_id']
    teaching_id = old_enrollment[0]['teaching_id']

    # 计算绩点
    grade_point = _get_grade_point(score)

    # 更新成绩
    execute(
        "UPDATE enrollments SET score = %s, grade_point = %s WHERE enroll_id = %s",
        (score, grade_point, enroll_id)
    )

    # 记录日志
    execute(
        """INSERT INTO enroll_logs(student_id, teaching_id, operation_type, old_value, new_value, operator, reason)
           VALUES(%s, %s, '成绩修改', %s, %s, %s, %s)""",
        (student_id, teaching_id, str(old_score) if old_score else '', str(score), operator, reason or '成绩录入/修改')
    )

    return jsonify({'code': 0, 'msg': '成绩录入成功'})


@api_teaching.route('/api/enrollment/batch_score', methods=['POST'])
def batch_update_score():
    """批量录入成绩"""
    data = request.get_json()
    scores = data.get('scores', [])  # [{enroll_id, score}, ...]
    operator = data.get('operator', '系统')

    success_count = 0
    fail_count = 0

    for item in scores:
        enroll_id = item.get('enroll_id')
        score = item.get('score')

        if score is not None:
            score = float(score)
            if score < 0 or score > 100:
                fail_count += 1
                continue

        # 获取原成绩
        old_enrollment = query("SELECT * FROM enrollments WHERE enroll_id = %s", (enroll_id,))
        if not old_enrollment:
            fail_count += 1
            continue

        old_score = old_enrollment[0]['score']
        student_id = old_enrollment[0]['student_id']
        teaching_id = old_enrollment[0]['teaching_id']

        # 计算绩点
        grade_point = _get_grade_point(score)

        # 更新成绩
        execute(
            "UPDATE enrollments SET score = %s, grade_point = %s WHERE enroll_id = %s",
            (score, grade_point, enroll_id)
        )

        # 记录日志
        execute(
            """INSERT INTO enroll_logs(student_id, teaching_id, operation_type, old_value, new_value, operator, reason)
               VALUES(%s, %s, '成绩修改', %s, %s, %s, '批量成绩录入')""",
            (student_id, teaching_id, str(old_score) if old_score else '', str(score), operator)
        )

        success_count += 1

    return jsonify({
        'code': 0,
        'msg': f'批量录入完成，成功{success_count}条，失败{fail_count}条',
        'success_count': success_count,
        'fail_count': fail_count
    })


@api_teaching.route('/api/students/<student_id>/scores', methods=['GET'])
def get_student_scores(student_id):
    """获取学生成绩单"""
    sql = """
        SELECT e.*, c.course_name, c.credits, c.type as course_type,
               te.name as teacher_name, t.classroom, t.schedule,
               s.academic_year, s.semester_name
        FROM enrollments e
        JOIN teaching t ON e.teaching_id = t.teaching_id
        JOIN courses c ON t.course_id = c.course_id
        JOIN teachers te ON t.teacher_id = te.teacher_id
        JOIN semesters s ON t.semester_id = s.semester_id
        WHERE e.student_id = %s AND e.score IS NOT NULL
        ORDER BY s.academic_year DESC, s.semester_name, c.course_id
    """
    rows = query(sql, (student_id,))

    # 计算总学分和平均绩点
    total_credits = sum(r['credits'] for r in rows if r['grade_point'] is not None)
    weighted_gp = sum(r['credits'] * r['grade_point'] for r in rows if r['grade_point'] is not None)
    avg_grade_point = weighted_gp / total_credits if total_credits > 0 else 0

    return jsonify({
        'code': 0,
        'data': rows,
        'summary': {
            'total_credits': round(total_credits, 1),
            'avg_grade_point': round(avg_grade_point, 2)
        }
    })


@api_teaching.route('/api/teaching/<int:teaching_id>/score_stats', methods=['GET'])
def get_teaching_score_stats(teaching_id):
    """获取课程成绩统计"""
    sql = """
        SELECT
            COUNT(*) as total_count,
            COUNT(CASE WHEN score >= 90 THEN 1 END) as a_count,
            COUNT(CASE WHEN score >= 80 AND score < 90 THEN 1 END) as b_count,
            COUNT(CASE WHEN score >= 70 AND score < 80 THEN 1 END) as c_count,
            COUNT(CASE WHEN score >= 60 AND score < 70 THEN 1 END) as d_count,
            COUNT(CASE WHEN score < 60 THEN 1 END) as f_count,
            AVG(score) as avg_score,
            MAX(score) as max_score,
            MIN(score) as min_score
        FROM enrollments
        WHERE teaching_id = %s AND score IS NOT NULL
    """
    stats = query(sql, (teaching_id,))

    return jsonify({'code': 0, 'data': stats[0] if stats else {}})
