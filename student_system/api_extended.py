"""
扩展功能API模块
提供宿舍管理、缴费管理、奖惩管理、培养计划管理接口
"""

import json

import pymysql
from flask import Blueprint, jsonify, request

from db_utils import build_filter_sql, execute, get_page_data, query

api_extended = Blueprint('api_extended', __name__)


# ============================================
# 宿舍管理API
# ============================================

@api_extended.route('/api/dorm_rooms', methods=['GET'])
def get_dorm_rooms():
    """获取宿舍房间列表，支持按楼栋筛选"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    building = request.args.get('building', '').strip()
    gender_limit = request.args.get('gender_limit', '').strip()
    has_vacancy = request.args.get('has_vacancy', type=int)
    filters_json = request.args.get('filters', '')

    base_sql = "SELECT * FROM dorm_rooms WHERE 1=1"
    params = []

    if filters_json:
        try:
            filters = json.loads(filters_json)
            filter_clause, filter_params = build_filter_sql(filters, {
                'building': 'building',
                'room_number': 'room_number',
                'capacity': 'capacity',
                'occupied': 'occupied',
                'gender_limit': 'gender_limit',
                'phone': 'phone'
            })
            base_sql += " " + filter_clause
            params.extend(filter_params)
        except (json.JSONDecodeError, TypeError):
            pass

    if building:
        base_sql += " AND building = %s"
        params.append(building)

    if gender_limit:
        base_sql += " AND gender_limit = %s"
        params.append(gender_limit)

    if has_vacancy:
        base_sql += " AND occupied < capacity"

    base_sql += " ORDER BY building, room_number"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/dorm_rooms', methods=['POST'])
def create_dorm_room():
    """新增宿舍房间"""
    data = request.get_json()
    building = data.get('building', '').strip()
    room_number = data.get('room_number', '').strip()
    capacity = data.get('capacity', 4)
    gender_limit = data.get('gender_limit', '不限')
    phone = data.get('phone', '').strip()

    if not building or not room_number:
        return jsonify({'code': 1, 'msg': '楼栋和房间号不能为空'})

    try:
        execute(
            "INSERT INTO dorm_rooms(building, room_number, capacity, gender_limit, phone) VALUES(%s, %s, %s, %s, %s)",
            (building, room_number, capacity, gender_limit, phone or None)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '该房间已存在'})


@api_extended.route('/api/dorm_rooms/<int:room_id>', methods=['PUT'])
def update_dorm_room(room_id):
    """更新宿舍房间信息"""
    data = request.get_json()
    capacity = data.get('capacity', 4)
    gender_limit = data.get('gender_limit', '不限')
    phone = data.get('phone', '').strip()

    execute(
        "UPDATE dorm_rooms SET capacity=%s, gender_limit=%s, phone=%s WHERE room_id=%s",
        (capacity, gender_limit, phone or None, room_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_extended.route('/api/dorm_rooms/<int:room_id>', methods=['DELETE'])
def delete_dorm_room(room_id):
    """删除宿舍房间（检查关联）"""
    # 检查是否有学生入住
    count = query("SELECT COUNT(*) AS cnt FROM dorm_assignments WHERE room_id = %s AND status = '在住'", (room_id,))
    if count and count[0]['cnt'] > 0:
        return jsonify({'code': 1, 'msg': '该房间有学生入住，无法删除'})

    execute("DELETE FROM dorm_rooms WHERE room_id = %s", (room_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


@api_extended.route('/api/dorm_buildings', methods=['GET'])
def get_dorm_buildings():
    """获取所有楼栋列表"""
    rows = query("SELECT DISTINCT building FROM dorm_rooms ORDER BY building")
    return jsonify({'code': 0, 'data': [r['building'] for r in rows]})


@api_extended.route('/api/dorm_assignments', methods=['GET'])
def get_dorm_assignments():
    """获取住宿分配列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    student_id = request.args.get('student_id', '').strip()
    room_id = request.args.get('room_id', type=int)
    status = request.args.get('status', '').strip()
    filters_json = request.args.get('filters', '')

    base_sql = """
        SELECT da.*, s.name as student_name, s.gender,
               dr.building, dr.room_number, dr.capacity, dr.occupied
        FROM dorm_assignments da
        JOIN students s ON da.student_id = s.student_id
        JOIN dorm_rooms dr ON da.room_id = dr.room_id
        WHERE 1=1
    """
    params = []

    if filters_json:
        try:
            filters = json.loads(filters_json)
            filter_clause, filter_params = build_filter_sql(filters, {
                'student_id': 'da.student_id',
                'student_name': 's.name',
                'gender': "CASE WHEN s.gender = 'M' THEN '男' WHEN s.gender = 'F' THEN '女' ELSE '' END",
                'building': 'dr.building',
                'room_number': 'dr.room_number',
                'bed_number': 'da.bed_number',
                'check_in_date': 'da.check_in_date',
                'status': 'da.status'
            })
            base_sql += " " + filter_clause
            params.extend(filter_params)
        except (json.JSONDecodeError, TypeError):
            pass

    if student_id:
        base_sql += " AND da.student_id = %s"
        params.append(student_id)

    if room_id:
        base_sql += " AND da.room_id = %s"
        params.append(room_id)

    if status:
        base_sql += " AND da.status = %s"
        params.append(status)

    base_sql += " ORDER BY da.check_in_date DESC"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/dorm_assignments', methods=['POST'])
def create_dorm_assignment():
    """分配宿舍"""
    data = request.get_json()
    student_id = data.get('student_id', '').strip()
    room_id = data.get('room_id', type=int)
    bed_number = data.get('bed_number', '').strip()
    check_in_date = data.get('check_in_date', '').strip()

    if not student_id or not room_id:
        return jsonify({'code': 1, 'msg': '学生和房间不能为空'})

    # 检查学生是否已有住宿
    existing = query(
        "SELECT * FROM dorm_assignments WHERE student_id = %s AND status = '在住'",
        (student_id,)
    )
    if existing:
        return jsonify({'code': 1, 'msg': '该学生已有住宿安排'})

    # 检查房间是否已满
    room = query("SELECT * FROM dorm_rooms WHERE room_id = %s", (room_id,))
    if not room:
        return jsonify({'code': 1, 'msg': '房间不存在'})

    if room[0]['occupied'] >= room[0]['capacity']:
        return jsonify({'code': 1, 'msg': '该房间已满'})

    try:
        execute(
            """INSERT INTO dorm_assignments(student_id, room_id, bed_number, check_in_date, status)
               VALUES(%s, %s, %s, %s, '在住')""",
            (student_id, room_id, bed_number or None, check_in_date or None)
        )
        return jsonify({'code': 0, 'msg': '分配成功'})
    except pymysql.err.IntegrityError as e:
        return jsonify({'code': 1, 'msg': f'分配失败：{str(e)}'})


@api_extended.route('/api/dorm_assignments/<int:assign_id>/checkout', methods=['POST'])
def checkout_dorm(assign_id):
    """退宿"""
    data = request.get_json()
    check_out_date = data.get('check_out_date', '').strip()
    remark = data.get('remark', '').strip()

    execute(
        """UPDATE dorm_assignments SET status='已退', check_out_date=%s, remark=%s WHERE assign_id=%s""",
        (check_out_date or None, remark or None, assign_id)
    )
    return jsonify({'code': 0, 'msg': '退宿成功'})


@api_extended.route('/api/dorm_rooms/available', methods=['GET'])
def get_available_dorm_rooms():
    """获取有空床位的房间"""
    gender = request.args.get('gender', '').strip()

    sql = """
        SELECT dr.*, (dr.capacity - dr.occupied) as available_beds
        FROM dorm_rooms dr
        WHERE dr.occupied < dr.capacity
    """
    params = []

    if gender:
        sql += " AND (dr.gender_limit = %s OR dr.gender_limit = '不限')"
        params.append(gender)

    sql += " ORDER BY dr.building, dr.room_number"

    rows = query(sql, params if params else None)
    return jsonify({'code': 0, 'data': rows})


# ============================================
# 缴费管理API
# ============================================

@api_extended.route('/api/payments', methods=['GET'])
def get_payments():
    """获取缴费记录列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    student_id = request.args.get('student_id', '').strip()
    academic_year = request.args.get('academic_year', '').strip()
    fee_type = request.args.get('fee_type', '').strip()
    status = request.args.get('status', '').strip()

    base_sql = """
        SELECT p.*, s.name as student_name, c.class_name
        FROM payments p
        JOIN students s ON p.student_id = s.student_id
        LEFT JOIN classes c ON s.class_id = c.class_id
        WHERE 1=1
    """
    params = []

    if student_id:
        base_sql += " AND p.student_id = %s"
        params.append(student_id)

    if academic_year:
        base_sql += " AND p.academic_year = %s"
        params.append(academic_year)

    if fee_type:
        base_sql += " AND p.fee_type = %s"
        params.append(fee_type)

    if status:
        base_sql += " AND p.status = %s"
        params.append(status)

    base_sql += " ORDER BY p.academic_year DESC, p.payment_id DESC"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/payments', methods=['POST'])
def create_payment():
    """新增费用记录"""
    data = request.get_json()
    student_id = data.get('student_id', '').strip()
    fee_type = data.get('fee_type', '').strip()
    academic_year = data.get('academic_year', '').strip()
    semester = data.get('semester', '').strip()
    amount_due = data.get('amount_due', 0)

    if not student_id or not fee_type or not academic_year:
        return jsonify({'code': 1, 'msg': '学生、费用类型和学年不能为空'})

    try:
        execute(
            """INSERT INTO payments(student_id, fee_type, academic_year, semester, amount_due)
               VALUES(%s, %s, %s, %s, %s)""",
            (student_id, fee_type, academic_year, semester or None, amount_due)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError as e:
        return jsonify({'code': 1, 'msg': f'新增失败：{str(e)}'})


@api_extended.route('/api/payments/<int:payment_id>/pay', methods=['POST'])
def record_payment(payment_id):
    """登记缴费"""
    data = request.get_json()
    amount_paid = data.get('amount_paid', 0)
    payment_date = data.get('payment_date', '').strip()
    payment_method = data.get('payment_method', '').strip()
    remark = data.get('remark', '').strip()

    # 获取当前缴费记录
    payment = query("SELECT * FROM payments WHERE payment_id = %s", (payment_id,))
    if not payment:
        return jsonify({'code': 1, 'msg': '缴费记录不存在'})

    current_paid = payment[0]['amount_paid'] or 0
    new_paid = current_paid + amount_paid
    amount_due = payment[0]['amount_due']

    # 更新缴费状态
    if new_paid >= amount_due:
        status = '已缴'
    elif new_paid > 0:
        status = '部分缴'
    else:
        status = '未缴'

    execute(
        """UPDATE payments SET amount_paid=%s, payment_date=%s, payment_method=%s,
           status=%s, remark=%s WHERE payment_id=%s""",
        (new_paid, payment_date or None, payment_method or None, status, remark or None, payment_id)
    )

    return jsonify({'code': 0, 'msg': '缴费登记成功'})


@api_extended.route('/api/payments/overdue', methods=['GET'])
def get_overdue_payments():
    """获取欠费学生列表"""
    academic_year = request.args.get('academic_year', '').strip()

    sql = """
        SELECT p.*, s.name as student_name, c.class_name,
               (p.amount_due - p.amount_paid) as amount_owed
        FROM payments p
        JOIN students s ON p.student_id = s.student_id
        LEFT JOIN classes c ON s.class_id = c.class_id
        WHERE p.status IN ('未缴', '部分缴')
    """
    params = []

    if academic_year:
        sql += " AND p.academic_year = %s"
        params.append(academic_year)

    sql += " ORDER BY p.academic_year DESC, amount_owed DESC"

    rows = query(sql, params if params else None)
    return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/payments/stats', methods=['GET'])
def get_payment_stats():
    """缴费统计"""
    academic_year = request.args.get('academic_year', '').strip()

    sql = """
        SELECT
            COUNT(*) as total_records,
            SUM(amount_due) as total_due,
            SUM(amount_paid) as total_paid,
            SUM(amount_due - amount_paid) as total_owed,
            COUNT(CASE WHEN status = '已缴' THEN 1 END) as paid_count,
            COUNT(CASE WHEN status = '部分缴' THEN 1 END) as partial_count,
            COUNT(CASE WHEN status = '未缴' THEN 1 END) as unpaid_count
        FROM payments
        WHERE 1=1
    """
    params = []

    if academic_year:
        sql += " AND academic_year = %s"
        params.append(academic_year)

    stats = query(sql, params if params else None)

    # 按费用类型统计
    type_sql = """
        SELECT fee_type,
               COUNT(*) as count,
               SUM(amount_due) as total_due,
               SUM(amount_paid) as total_paid
        FROM payments
        WHERE 1=1
    """
    if academic_year:
        type_sql += " AND academic_year = %s"
    type_sql += " GROUP BY fee_type"

    type_stats = query(type_sql, params if params else None)

    return jsonify({
        'code': 0,
        'data': {
            'summary': stats[0] if stats else {},
            'by_type': type_stats
        }
    })


# ============================================
# 奖惩管理API
# ============================================

@api_extended.route('/api/rewards_punishments', methods=['GET'])
def get_rewards_punishments():
    """获取奖惩记录列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    student_id = request.args.get('student_id', '').strip()
    rp_type = request.args.get('type', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    base_sql = """
        SELECT rp.*, s.name as student_name, c.class_name
        FROM rewards_punishments rp
        JOIN students s ON rp.student_id = s.student_id
        LEFT JOIN classes c ON s.class_id = c.class_id
        WHERE 1=1
    """
    params = []

    if student_id:
        base_sql += " AND rp.student_id = %s"
        params.append(student_id)

    if rp_type:
        base_sql += " AND rp.rp_type = %s"
        params.append(rp_type)

    if start_date:
        base_sql += " AND rp.date >= %s"
        params.append(start_date)

    if end_date:
        base_sql += " AND rp.date <= %s"
        params.append(end_date)

    base_sql += " ORDER BY rp.date DESC"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/rewards_punishments', methods=['POST'])
def create_reward_punishment():
    """新增奖惩记录"""
    data = request.get_json()
    student_id = data.get('student_id', '').strip()
    rp_type = data.get('rp_type', '').strip()
    title = data.get('title', '').strip()
    level = data.get('level', '').strip()
    date = data.get('date', '').strip()
    reason = data.get('reason', '').strip()
    issuing_authority = data.get('issuing_authority', '').strip()

    if not student_id or not rp_type or not title or not date:
        return jsonify({'code': 1, 'msg': '学生、类型、名称和日期不能为空'})

    execute(
        """INSERT INTO rewards_punishments(student_id, rp_type, title, level, date, reason, issuing_authority)
           VALUES(%s, %s, %s, %s, %s, %s, %s)""",
        (student_id, rp_type, title, level or None, date, reason or None, issuing_authority or None)
    )
    return jsonify({'code': 0, 'msg': '新增成功'})


@api_extended.route('/api/rewards_punishments/<int:rp_id>', methods=['PUT'])
def update_reward_punishment(rp_id):
    """更新奖惩记录"""
    data = request.get_json()
    title = data.get('title', '').strip()
    level = data.get('level', '').strip()
    reason = data.get('reason', '').strip()
    issuing_authority = data.get('issuing_authority', '').strip()
    remark = data.get('remark', '').strip()

    execute(
        """UPDATE rewards_punishments SET title=%s, level=%s, reason=%s,
           issuing_authority=%s, remark=%s WHERE rp_id=%s""",
        (title, level or None, reason or None, issuing_authority or None, remark or None, rp_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_extended.route('/api/rewards_punishments/<int:rp_id>', methods=['DELETE'])
def delete_reward_punishment(rp_id):
    """删除奖惩记录"""
    execute("DELETE FROM rewards_punishments WHERE rp_id = %s", (rp_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


@api_extended.route('/api/students/<student_id>/rewards_punishments', methods=['GET'])
def get_student_rewards_punishments(student_id):
    """获取学生奖惩历史"""
    rows = query(
        """SELECT * FROM rewards_punishments WHERE student_id = %s ORDER BY date DESC""",
        (student_id,)
    )
    return jsonify({'code': 0, 'data': rows})


# ============================================
# 培养计划管理API
# ============================================

@api_extended.route('/api/curriculum', methods=['GET'])
def get_curriculum():
    """获取培养计划列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    major_id = request.args.get('major_id', type=int)
    enrollment_year = request.args.get('enrollment_year', type=int)

    base_sql = """
        SELECT c.*, m.major_name, co.course_name, co.credits, co.hours, co.type as course_type
        FROM curriculum c
        JOIN majors m ON c.major_id = m.major_id
        JOIN courses co ON c.course_id = co.course_id
        WHERE 1=1
    """
    params = []

    if major_id:
        base_sql += " AND c.major_id = %s"
        params.append(major_id)

    if enrollment_year:
        base_sql += " AND c.enrollment_year = %s"
        params.append(enrollment_year)

    base_sql += " ORDER BY c.enrollment_year DESC, c.major_id, c.recommended_term, c.course_id"

    if page > 0:
        result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
        return jsonify({'code': 0, 'data': result['data'], 'total': result['total'],
                       'page': result['page'], 'total_pages': result['total_pages']})
    else:
        rows = query(base_sql, params if params else None)
        return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/curriculum', methods=['POST'])
def create_curriculum():
    """添加课程到培养计划"""
    data = request.get_json()
    major_id = data.get('major_id', type=int)
    enrollment_year = data.get('enrollment_year', type=int)
    course_id = data.get('course_id', '').strip()
    course_type = data.get('course_type', '必修')
    recommended_term = data.get('recommended_term', '').strip()
    min_grade = data.get('min_grade')
    is_core = data.get('is_core', False)

    if not major_id or not enrollment_year or not course_id:
        return jsonify({'code': 1, 'msg': '专业、入学年份和课程不能为空'})

    try:
        execute(
            """INSERT INTO curriculum(major_id, enrollment_year, course_id, course_type, recommended_term, min_grade, is_core)
               VALUES(%s, %s, %s, %s, %s, %s, %s)""",
            (major_id, enrollment_year, course_id, course_type, recommended_term or None, min_grade, is_core)
        )
        return jsonify({'code': 0, 'msg': '添加成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '该课程已存在于培养计划中'})


@api_extended.route('/api/curriculum/<int:plan_id>', methods=['PUT'])
def update_curriculum(plan_id):
    """更新培养计划项"""
    data = request.get_json()
    course_type = data.get('course_type', '必修')
    recommended_term = data.get('recommended_term', '').strip()
    min_grade = data.get('min_grade')
    is_core = data.get('is_core', False)
    remark = data.get('remark', '').strip()

    execute(
        """UPDATE curriculum SET course_type=%s, recommended_term=%s, min_grade=%s, is_core=%s, remark=%s
           WHERE plan_id=%s""",
        (course_type, recommended_term or None, min_grade, is_core, remark or None, plan_id)
    )
    return jsonify({'code': 0, 'msg': '更新成功'})


@api_extended.route('/api/curriculum/<int:plan_id>', methods=['DELETE'])
def delete_curriculum(plan_id):
    """删除培养计划项"""
    execute("DELETE FROM curriculum WHERE plan_id = %s", (plan_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


@api_extended.route('/api/students/<student_id>/curriculum', methods=['GET'])
def get_student_curriculum(student_id):
    """获取学生个人培养计划"""
    # 获取学生信息
    student = query(
        """SELECT s.*, c.major_id, c.enrollment_year
           FROM students s
           JOIN classes c ON s.class_id = c.class_id
           WHERE s.student_id = %s""",
        (student_id,)
    )

    if not student:
        return jsonify({'code': 1, 'msg': '学生不存在'})

    major_id = student[0]['major_id']
    enrollment_year = student[0]['enrollment_year']

    # 获取培养计划及修读状态
    sql = """
        SELECT c.*, co.course_name, co.credits, co.hours, co.type as course_type,
               e.score, e.grade_point, e.status as enroll_status
        FROM curriculum c
        JOIN courses co ON c.course_id = co.course_id
        LEFT JOIN teaching t ON co.course_id = t.course_id
        LEFT JOIN enrollments e ON t.teaching_id = e.teaching_id AND e.student_id = %s
        WHERE c.major_id = %s AND c.enrollment_year = %s
        ORDER BY c.recommended_term, c.course_id
    """
    rows = query(sql, (student_id, major_id, enrollment_year))

    # 计算学分完成情况
    total_credits = sum(r['credits'] for r in rows)
    earned_credits = sum(r['credits'] for r in rows if r['score'] and r['score'] >= 60)

    return jsonify({
        'code': 0,
        'data': rows,
        'summary': {
            'total_credits': total_credits,
            'earned_credits': earned_credits,
            'remaining_credits': total_credits - earned_credits
        }
    })


# ============================================
# 数据统计API
# ============================================

@api_extended.route('/api/statistics/students', methods=['GET'])
def get_student_statistics():
    """学生人数统计（按院系/专业/班级）"""
    group_by = request.args.get('group_by', 'department').strip()

    if group_by == 'department':
        sql = """
            SELECT d.dept_name as name, COUNT(s.student_id) as count
            FROM departments d
            LEFT JOIN majors m ON d.dept_id = m.dept_id
            LEFT JOIN classes c ON m.major_id = c.major_id
            LEFT JOIN students s ON c.class_id = s.class_id
            GROUP BY d.dept_id, d.dept_name
            ORDER BY count DESC
        """
    elif group_by == 'major':
        sql = """
            SELECT m.major_name as name, d.dept_name as parent_name, COUNT(s.student_id) as count
            FROM majors m
            JOIN departments d ON m.dept_id = d.dept_id
            LEFT JOIN classes c ON m.major_id = c.major_id
            LEFT JOIN students s ON c.class_id = s.class_id
            GROUP BY m.major_id, m.major_name, d.dept_name
            ORDER BY count DESC
        """
    elif group_by == 'class':
        sql = """
            SELECT c.class_name as name, m.major_name as parent_name, COUNT(s.student_id) as count
            FROM classes c
            JOIN majors m ON c.major_id = m.major_id
            LEFT JOIN students s ON c.class_id = s.class_id
            GROUP BY c.class_id, c.class_name, m.major_name
            ORDER BY count DESC
        """
    else:
        return jsonify({'code': 1, 'msg': '不支持的统计维度'})

    rows = query(sql)
    return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/statistics/gender', methods=['GET'])
def get_gender_statistics():
    """学生性别比例统计"""
    # 全校性别统计
    total_sql = """
        SELECT gender, COUNT(*) as count
        FROM students
        WHERE gender IS NOT NULL AND gender != ''
        GROUP BY gender
    """
    total_stats = query(total_sql)

    # 按院系性别统计
    dept_sql = """
        SELECT d.dept_name, s.gender, COUNT(*) as count
        FROM students s
        JOIN classes c ON s.class_id = c.class_id
        JOIN majors m ON c.major_id = m.major_id
        JOIN departments d ON m.dept_id = d.dept_id
        WHERE s.gender IS NOT NULL AND s.gender != ''
        GROUP BY d.dept_id, d.dept_name, s.gender
        ORDER BY d.dept_name
    """
    dept_stats = query(dept_sql)

    return jsonify({
        'code': 0,
        'data': {
            'total': total_stats,
            'by_department': dept_stats
        }
    })


@api_extended.route('/api/statistics/student_status', methods=['GET'])
def get_student_status_statistics():
    """学生状态分布统计"""
    sql = """
        SELECT status, COUNT(*) as count
        FROM students
        GROUP BY status
        ORDER BY count DESC
    """
    rows = query(sql)
    return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/statistics/grades', methods=['GET'])
def get_grade_statistics():
    """课程成绩分布统计"""
    teaching_id = request.args.get('teaching_id', type=int)
    course_id = request.args.get('course_id', '').strip()

    if not teaching_id and not course_id:
        return jsonify({'code': 1, 'msg': '请提供授课ID或课程ID'})

    if teaching_id:
        # 特定授课班级的成绩分布
        sql = """
            SELECT
                CASE
                    WHEN score >= 90 THEN '优秀(90-100)'
                    WHEN score >= 80 THEN '良好(80-89)'
                    WHEN score >= 70 THEN '中等(70-79)'
                    WHEN score >= 60 THEN '及格(60-69)'
                    ELSE '不及格(0-59)'
                END as grade_range,
                COUNT(*) as count,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score
            FROM enrollments
            WHERE teaching_id = %s AND score IS NOT NULL
            GROUP BY grade_range
            ORDER BY min_score DESC
        """
        params = (teaching_id,)

        # 获取课程基本信息
        course_info = query("""
            SELECT co.course_name, t.semester_id, s.name as teacher_name
            FROM teaching t
            JOIN courses co ON t.course_id = co.course_id
            LEFT JOIN teachers s ON t.teacher_id = s.teacher_id
            WHERE t.teaching_id = %s
        """, (teaching_id,))
    else:
        # 按课程统计所有学期的成绩分布
        sql = """
            SELECT
                CASE
                    WHEN e.score >= 90 THEN '优秀(90-100)'
                    WHEN e.score >= 80 THEN '良好(80-89)'
                    WHEN e.score >= 70 THEN '中等(70-79)'
                    WHEN e.score >= 60 THEN '及格(60-69)'
                    ELSE '不及格(0-59)'
                END as grade_range,
                COUNT(*) as count,
                AVG(e.score) as avg_score,
                MAX(e.score) as max_score,
                MIN(e.score) as min_score
            FROM enrollments e
            JOIN teaching t ON e.teaching_id = t.teaching_id
            WHERE t.course_id = %s AND e.score IS NOT NULL
            GROUP BY grade_range
            ORDER BY min_score DESC
        """
        params = (course_id,)

        # 获取课程基本信息
        course_info = query("SELECT course_name FROM courses WHERE course_id = %s", (course_id,))

    distribution = query(sql, params)

    return jsonify({
        'code': 0,
        'data': {
            'course_info': course_info[0] if course_info else {},
            'distribution': distribution
        }
    })


@api_extended.route('/api/statistics/class_grades', methods=['GET'])
def get_class_grade_statistics():
    """班级平均成绩对比"""
    semester_id = request.args.get('semester_id', type=int)

    sql = """
        SELECT
            c.class_name,
            m.major_name,
            d.dept_name,
            COUNT(DISTINCT e.student_id) as student_count,
            AVG(e.score) as avg_score,
            AVG(e.grade_point) as avg_gpa
        FROM enrollments e
        JOIN teaching t ON e.teaching_id = t.teaching_id
        JOIN students s ON e.student_id = s.student_id
        JOIN classes c ON s.class_id = c.class_id
        JOIN majors m ON c.major_id = m.major_id
        JOIN departments d ON m.dept_id = d.dept_id
        WHERE e.score IS NOT NULL
    """
    params = []

    if semester_id:
        sql += " AND t.semester_id = %s"
        params.append(semester_id)

    sql += """
        GROUP BY c.class_id, c.class_name, m.major_name, d.dept_name
        ORDER BY avg_score DESC
    """

    rows = query(sql, params if params else None)
    return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/statistics/gpa_ranking', methods=['GET'])
def get_gpa_ranking():
    """学生绩点排名"""
    class_id = request.args.get('class_id', type=int)
    major_id = request.args.get('major_id', type=int)
    limit = request.args.get('limit', 50, type=int)

    sql = """
        SELECT
            s.student_id,
            s.name,
            c.class_name,
            m.major_name,
            AVG(e.grade_point) as avg_gpa,
            SUM(co.credits) as total_credits,
            COUNT(e.enrollment_id) as course_count
        FROM students s
        JOIN classes c ON s.class_id = c.class_id
        JOIN majors m ON c.major_id = m.major_id
        JOIN enrollments e ON s.student_id = e.student_id
        JOIN teaching t ON e.teaching_id = t.teaching_id
        JOIN courses co ON t.course_id = co.course_id
        WHERE e.score IS NOT NULL
    """
    params = []

    if class_id:
        sql += " AND s.class_id = %s"
        params.append(class_id)

    if major_id:
        sql += " AND c.major_id = %s"
        params.append(major_id)

    sql += """
        GROUP BY s.student_id, s.name, c.class_name, m.major_name
        ORDER BY avg_gpa DESC
        LIMIT %s
    """
    params.append(limit)

    rows = query(sql, params)

    # 添加排名
    for i, row in enumerate(rows, 1):
        row['rank'] = i

    return jsonify({'code': 0, 'data': rows})


@api_extended.route('/api/statistics/dashboard', methods=['GET'])
def get_dashboard_statistics():
    """仪表盘综合统计数据"""
    # 学生总数
    student_count = query("SELECT COUNT(*) as count FROM students")
    # 教师总数
    teacher_count = query("SELECT COUNT(*) as count FROM teachers")
    # 课程总数
    course_count = query("SELECT COUNT(*) as count FROM courses")
    # 院系总数
    dept_count = query("SELECT COUNT(*) as count FROM departments")
    # 班级总数
    class_count = query("SELECT COUNT(*) as count FROM classes")

    # 本学期选课人数
    current_semester = query("SELECT semester_id FROM semesters WHERE is_current = TRUE LIMIT 1")
    enrollment_count = 0
    if current_semester:
        enrollment_result = query(
            "SELECT COUNT(*) as count FROM enrollments e JOIN teaching t ON e.teaching_id = t.teaching_id WHERE t.semester_id = %s",
            (current_semester[0]['semester_id'],)
        )
        enrollment_count = enrollment_result[0]['count'] if enrollment_result else 0

    # 宿舍入住率
    dorm_stats = query("""
        SELECT
            SUM(capacity) as total_capacity,
            SUM(occupied) as total_occupied,
            COUNT(*) as total_rooms
        FROM dorm_rooms
    """)

    # 缴费统计
    payment_stats = query("""
        SELECT
            SUM(amount_due) as total_due,
            SUM(amount_paid) as total_paid,
            COUNT(CASE WHEN status = '未缴' THEN 1 END) as unpaid_count
        FROM payments
    """)

    return jsonify({
        'code': 0,
        'data': {
            'overview': {
                'student_count': student_count[0]['count'] if student_count else 0,
                'teacher_count': teacher_count[0]['count'] if teacher_count else 0,
                'course_count': course_count[0]['count'] if course_count else 0,
                'dept_count': dept_count[0]['count'] if dept_count else 0,
                'class_count': class_count[0]['count'] if class_count else 0,
                'current_enrollment_count': enrollment_count
            },
            'dormitory': dorm_stats[0] if dorm_stats else {},
            'payment': payment_stats[0] if payment_stats else {}
        }
    })
