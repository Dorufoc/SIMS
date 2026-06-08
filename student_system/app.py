"""
学生信息管理系统 - Flask应用入口
提供用户认证、学生信息CRUD、CSV导入导出等功能
"""

from functools import wraps

import math
import pymysql

from flask import Flask, jsonify, redirect, render_template, request, send_file, session

from api_basic import api_basic
from api_teaching import api_teaching
from api_extended import api_extended
from config import SECRET_KEY
import csv_handle
from db_utils import execute, get_page_data, query
import permission_utils
import password_utils


app = Flask(__name__)
app.secret_key = SECRET_KEY

# 注册API蓝图
app.register_blueprint(api_basic)
app.register_blueprint(api_teaching)
app.register_blueprint(api_extended)


# ============================================
# 全局登录拦截器
# ============================================

@app.before_request
def check_login():
    """未登录用户拦截，白名单路由放行"""
    white_list = ['/login', '/register']
    path = request.path

    # 白名单路由放行
    if path in white_list or path.startswith('/static'):
        return None

    # 检查session中是否有user_id
    if 'user_id' not in session:
        return redirect('/login')


# ============================================
# 用户认证路由
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    rows = query(
        'SELECT user_id, username, role, ref_id, uuid, password_hash FROM users WHERE username=%s',
        (username,)
    )

    if rows:
        user = rows[0]
        
        # 验证密码
        if password_utils.verify_password(password, user['password_hash']):
            session['user_id'] = user['user_id']
            session['user_name'] = user['username']
            session['user_role'] = user['role']
            session['user_ref_id'] = user['ref_id']
            session['user_uuid'] = user['uuid']

            # 更新最后登录时间
            execute('UPDATE users SET last_login = NOW() WHERE user_id = %s', (user['user_id'],))

            return jsonify({'code': 0, 'msg': '登录成功', 'role': user['role']})
        else:
            return jsonify({'code': 1, 'msg': '用户名或密码错误'})
    else:
        return jsonify({'code': 1, 'msg': '用户名或密码错误'})


@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    real_name = request.form.get('real_name', '').strip()
    role = request.form.get('role', 'student').strip()
    ref_id = request.form.get('ref_id', '').strip()

    # 验证角色有效性
    if role not in ['admin', 'teacher', 'student']:
        role = 'student'

    try:
        user_uuid = permission_utils.generate_uuid()
        encrypted_password = password_utils.encrypt_password(password)
        execute(
            'INSERT INTO users(uuid, username, password_hash, role, ref_id) VALUES(%s, %s, %s, %s, %s)',
            (user_uuid, username, encrypted_password, role, ref_id or None)
        )
        # 初始化新用户权限
        permission_utils.initialize_user_permissions(user_uuid)
        return jsonify({'code': 0, 'msg': '注册成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '账号已被注册'})


@app.route('/logout')
def logout():
    """退出登录，清除session"""
    session.clear()
    return redirect('/login')


# ============================================
# 学生CRUD路由
# ============================================

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


# ============================================
# 基础数据管理页面路由
# ============================================

@app.route('/departments')
def departments_page():
    """院系管理页面"""
    return render_template('departments.html')


@app.route('/majors')
def majors_page():
    """专业管理页面"""
    return render_template('majors.html')


@app.route('/classes')
def classes_page():
    """班级管理页面"""
    return render_template('classes.html')


@app.route('/teachers')
def teachers_page():
    """教师管理页面"""
    return render_template('teachers.html')


@app.route('/courses')
def courses_page():
    """课程管理页面"""
    return render_template('courses.html')


# ============================================
# 扩展功能页面路由
# ============================================

@app.route('/dorm_rooms')
def dorm_rooms_page():
    """宿舍管理页面"""
    return render_template('dorm_rooms.html')


@app.route('/dorm_assignments')
def dorm_assignments_page():
    """住宿分配页面"""
    return render_template('dorm_assignments.html')


@app.route('/statistics')
def statistics_page():
    """统计报表页面"""
    return render_template('statistics.html')


@app.route('/add', methods=['GET', 'POST'])
def add_student():
    """新增学生"""
    if request.method == 'GET':
        return render_template('add_stu.html')

    student_id = request.form.get('student_id', '').strip()
    name = request.form.get('name', '').strip()
    gender = request.form.get('gender', '').strip()
    birth_date = request.form.get('birth_date', '').strip()
    id_card_no = request.form.get('id_card_no', '').strip()
    enrollment_year = request.form.get('enrollment_year', '').strip()
    dept_id = request.form.get('dept_id', '').strip()
    class_id = request.form.get('class_id', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()

    # 转换数据类型
    enrollment_year_val = int(enrollment_year) if enrollment_year else None
    dept_id_val = int(dept_id) if dept_id else None
    class_id_val = int(class_id) if class_id else None

    try:
        execute(
            """INSERT INTO students(student_id, name, gender, birth_date, id_card_no, enrollment_year,
               dept_id, class_id, phone, email, address, status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'在校')""",
            (student_id, name, gender or None, birth_date or None, id_card_no or None,
             enrollment_year_val, dept_id_val, class_id_val, phone or None, email or None, address or None)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '学号已存在'})


@app.route('/manage')
def manage():
    """数据管理（分页展示）"""
    page = request.args.get('page', 1, type=int)
    base_sql = """
        SELECT s.student_id, s.name, s.gender, s.birth_date, s.enrollment_year,
               s.status, s.phone, s.email,
               c.class_name, c.enrollment_year as class_year,
               m.major_name, d.dept_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.class_id
        LEFT JOIN majors m ON c.major_id = m.major_id
        LEFT JOIN departments d ON m.dept_id = d.dept_id
    """
    page_data = get_page_data(base_sql, page=page)
    return render_template(
        'manage.html',
        data=page_data['data'],
        page=page_data['page'],
        total_pages=page_data['total_pages']
    )


@app.route('/edit/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """编辑学生信息"""
    if request.method == 'GET':
        sql = """
            SELECT s.*, c.class_name, m.major_name, d.dept_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            LEFT JOIN majors m ON c.major_id = m.major_id
            LEFT JOIN departments d ON m.dept_id = d.dept_id
            WHERE s.student_id = %s
        """
        rows = query(sql, (student_id,))
        return jsonify(rows[0]) if rows else jsonify({})

    name = request.form.get('name', '').strip()
    gender = request.form.get('gender', '').strip()
    birth_date = request.form.get('birth_date', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    status = request.form.get('status', '').strip()
    class_id = request.form.get('class_id', '').strip()

    class_id_val = int(class_id) if class_id else None

    execute(
        """UPDATE students SET name=%s, gender=%s, birth_date=%s, phone=%s,
           email=%s, address=%s, status=%s, class_id=%s WHERE student_id=%s""",
        (name, gender or None, birth_date or None, phone or None,
         email or None, address or None, status or '在校', class_id_val, student_id)
    )
    return jsonify({'code': 0, 'msg': '修改成功'})


@app.route('/delete/<student_id>', methods=['POST'])
def delete_student(student_id):
    """删除学生"""
    execute('DELETE FROM students WHERE student_id=%s', (student_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


# ============================================
# CSV导入导出路由
# ============================================

@app.route('/csv/template')
def csv_template():
    """下载CSV模板"""
    template = csv_handle.generate_template()
    return send_file(template, as_attachment=True, download_name='student_template.csv', mimetype='text/csv')


@app.route('/csv/preview', methods=['POST'])
def csv_preview():
    """CSV文件预览与校验"""
    file = request.files['file']
    result = csv_handle.parse_csv(file)
    return jsonify({'valid_data': result['valid_data'], 'errors': result['errors']})


@app.route('/csv/import', methods=['POST'])
def csv_import():
    """CSV批量导入"""
    valid_data = request.get_json().get('valid_data', [])
    try:
        count = csv_handle.import_data(valid_data)
        return jsonify({'code': 0, 'msg': '导入成功', 'count': count})
    except Exception as e:
        return jsonify({'code': 1, 'msg': f'导入失败：{e}'})


@app.route('/csv/export')
def csv_export():
    """全量导出CSV"""
    csv_data = csv_handle.export_csv()
    return send_file(csv_data, as_attachment=True, download_name='student_data.csv', mimetype='text/csv')


@app.route('/csv/export_filtered', methods=['GET', 'POST'])
def csv_export_filtered():
    """按条件筛选导出CSV"""
    if request.method == 'GET':
        query_sql = request.args.get('sql')
    else:
        query_sql = request.form.get('query_sql')
    csv_data = csv_handle.export_csv(query_sql)
    return send_file(csv_data, as_attachment=True, download_name='student_data.csv', mimetype='text/csv')


# ============================================
# 数据接口路由（用于下拉选择器）
# ============================================

@app.route('/api/departments', methods=['GET'])
def api_departments():
    """获取学院列表"""
    rows = query("SELECT dept_id, dept_name FROM departments ORDER BY dept_name")
    return jsonify(rows)


@app.route('/api/majors', methods=['GET'])
def api_majors():
    """获取专业列表，可按学院筛选"""
    dept_id = request.args.get('dept_id')
    if dept_id:
        rows = query("SELECT major_id, major_name FROM majors WHERE dept_id = %s ORDER BY major_name", (dept_id,))
    else:
        rows = query("SELECT major_id, major_name FROM majors ORDER BY major_name")
    return jsonify(rows)


@app.route('/api/classes', methods=['GET'])
def api_classes():
    """获取班级列表，可按专业筛选"""
    major_id = request.args.get('major_id')
    if major_id:
        rows = query("SELECT class_id, class_name, grade FROM classes WHERE major_id = %s ORDER BY class_name", (major_id,))
    else:
        rows = query("SELECT class_id, class_name, grade FROM classes ORDER BY class_name")
    return jsonify(rows)


# ============================================
# 高级查询路由
# ============================================

# SQL映射表
SQL_MAP = {
    # 条件筛选类
    'AND': "SELECT * FROM student_info WHERE major='计算机' AND grade='2022'",
    'OR': "SELECT * FROM student_info WHERE major='计算机' OR major='软件工程'",
    'NOT': "SELECT * FROM student_info WHERE NOT major='计算机'",
    'IS_NULL': "SELECT * FROM student_info WHERE class_name IS NULL",
    'IS_NOT_NULL': "SELECT * FROM student_info WHERE age IS NOT NULL",
    'BETWEEN': "SELECT * FROM student_info WHERE age BETWEEN 18 AND 22",
    'IN': "SELECT * FROM student_info WHERE major IN('计算机','自动化','汉语言')",
    'NOT_IN': "SELECT * FROM student_info WHERE major NOT IN('计算机','自动化','汉语言')",
    'LIKE': "SELECT * FROM student_info WHERE student_name LIKE '%张%'",
    'LIKE_WILDCARD': "SELECT * FROM student_info WHERE student_name LIKE '张_'",
    # 聚合统计类
    'GROUP_BY': "SELECT major AS 专业,COUNT(*) AS 人数 FROM student_info GROUP BY major",
    'HAVING': "SELECT major AS 专业,COUNT(*) AS 人数 FROM student_info GROUP BY major HAVING COUNT(*)>10",
    'COUNT': "SELECT COUNT(*) AS 总人数, COUNT(age) AS 有年龄人数 FROM student_info",
    'SUM': "SELECT SUM(age) AS 年龄总和 FROM student_info",
    'AVG': "SELECT major AS 专业,AVG(age) AS 平均年龄 FROM student_info GROUP BY major",
    'MAX_MIN': "SELECT major AS 专业,MAX(age) AS 最大年龄,MIN(age) AS 最小年龄 FROM student_info GROUP BY major",
    # 排序分页去重类
    'ORDER_ASC': "SELECT * FROM student_info ORDER BY student_no ASC LIMIT 20",
    'ORDER_DESC': "SELECT * FROM student_info ORDER BY age DESC LIMIT 20",
    'LIMIT_PAGE': "SELECT * FROM student_info LIMIT 0,10",
    'DISTINCT': "SELECT DISTINCT major AS 不重复专业 FROM student_info",
    # 运算符别名类
    'AS': "SELECT student_name AS 姓名, major AS 专业, age AS 年龄 FROM student_info LIMIT 10",
    'COMPARE': "SELECT * FROM student_info WHERE age>20 LIMIT 10",
    # DDL类
    'CREATE_DATABASE': "CREATE DATABASE IF NOT EXISTS student_manage DEFAULT CHARACTER SET utf8;",
    'DROP_DATABASE': "DROP DATABASE IF EXISTS student_manage",
    'CREATE_TABLE': (
        "CREATE TABLE IF NOT EXISTS student_info (\n"
        "  id INT AUTO_INCREMENT PRIMARY KEY,\n"
        "  student_no VARCHAR(20) NOT NULL UNIQUE COMMENT '学号',\n"
        "  student_name VARCHAR(50) NOT NULL COMMENT '姓名',\n"
        "  gender VARCHAR(10) DEFAULT NULL COMMENT '性别',\n"
        "  age INT DEFAULT NULL COMMENT '年龄',\n"
        "  major VARCHAR(50) DEFAULT NULL COMMENT '专业',\n"
        "  grade VARCHAR(20) DEFAULT NULL COMMENT '年级',\n"
        "  class_name VARCHAR(50) DEFAULT NULL COMMENT '班级'\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生信息表';\n\n"
        "CREATE TABLE IF NOT EXISTS user_info (\n"
        "  uid INT AUTO_INCREMENT PRIMARY KEY,\n"
        "  username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',\n"
        "  password VARCHAR(100) NOT NULL COMMENT '密码',\n"
        "  real_name VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',\n"
        "  role VARCHAR(20) DEFAULT 'user' COMMENT '角色'\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';"
    ),
    'DROP_TABLE': "DROP TABLE IF EXISTS student_info",
    'ALTER_TABLE': "ALTER TABLE student_info ADD COLUMN phone VARCHAR(20) DEFAULT NULL COMMENT '联系电话'",
    'COMMENT': (
        "MySQL注释用法说明：\n\n"
        "1. 建表时字段注释：\n"
        "   student_no VARCHAR(20) COMMENT '学号'\n\n"
        "2. 建表时表注释：\n"
        "   CREATE TABLE ... COMMENT='学生信息表'\n\n"
        "3. SQL中的单行注释：\n"
        "   -- 这是单行注释\n\n"
        "4. SQL中的多行注释：\n"
        "   /* 这是多行注释 */"
    ),
    'ENGINE_CHARSET': (
        "MySQL引擎与字符集说明：\n\n"
        "1. 存储引擎：ENGINE=InnoDB\n"
        "   InnoDB：支持事务、行级锁、外键，适合高并发\n"
        "   MyISAM：不支持事务，表级锁，适合读多写少\n\n"
        "2. 字符集：DEFAULT CHARSET=utf8mb4\n"
        "   utf8mb4：完整Unicode支持（含emoji），推荐使用\n"
        "   utf8：仅支持3字节Unicode，部分字符无法存储\n\n"
        "3. 排序规则：COLLATE=utf8mb4_general_ci\n"
        "   _general_ci：不区分大小写，查询速度快\n"
        "   _bin：区分大小写，精确匹配"
    ),
    # DML类
    'INSERT': (
        "INSERT语句示例：\n\n"
        "INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name)\n"
        "VALUES('2024001','张三','男',20,'计算机','2024','计科1班');"
    ),
    'INSERT_MULTI': (
        "多值INSERT语句示例：\n\n"
        "INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name)\n"
        "VALUES\n"
        "  ('2024001','张三','男',20,'计算机','2024','计科1班'),\n"
        "  ('2024002','李四','女',21,'软件工程','2024','软工1班'),\n"
        "  ('2024003','王五','男',19,'自动化','2024','自控1班');"
    ),
    'UPDATE': (
        "UPDATE语句示例：\n\n"
        "UPDATE student_info SET major='软件工程', grade='2024' WHERE student_no='2024001';"
    ),
    'DELETE': (
        "DELETE语句示例：\n\n"
        "DELETE FROM student_info WHERE student_no='2024001';"
    ),
    'SELECT': (
        "SELECT语句示例：\n\n"
        "SELECT student_no, student_name, major FROM student_info WHERE major='计算机' LIMIT 10;"
    ),
    'FROM': (
        "FROM子句示例：\n\n"
        "SELECT * FROM student_info;\n"
        "SELECT COUNT(*) FROM student_info;"
    ),
    'WHERE': (
        "WHERE子句示例：\n\n"
        "SELECT * FROM student_info WHERE major='计算机' AND age>18;"
    ),
    # 事务约束类
    'PRIMARY_KEY': (
        "PRIMARY KEY（主键）约束说明：\n\n"
        "主键用于唯一标识表中的每条记录，具有以下特性：\n"
        "1. 唯一且不为NULL\n"
        "2. 每个表只能有一个主键\n"
        "3. 自动创建索引\n\n"
        "示例：\n"
        "CREATE TABLE example (\n"
        "  id INT AUTO_INCREMENT PRIMARY KEY,\n"
        "  name VARCHAR(50)\n"
        ");\n\n"
        "或：ALTER TABLE example ADD PRIMARY KEY (id);"
    ),
    'AUTO_INCREMENT': (
        "AUTO_INCREMENT（自增）说明：\n\n"
        "自增字段自动为每条新记录生成唯一递增值：\n"
        "1. 一个表只能有一个自增字段\n"
        "2. 必须是主键或唯一键的一部分\n"
        "3. 删除记录后，已用值不会被复用\n\n"
        "示例：\n"
        "CREATE TABLE example (\n"
        "  id INT AUTO_INCREMENT PRIMARY KEY\n"
        ");"
    ),
    'UNIQUE': (
        "UNIQUE（唯一）约束说明：\n\n"
        "唯一约束确保列中的值不重复，允许NULL值：\n"
        "1. 一个表可以有多个唯一约束\n"
        "2. 允许NULL值（多个NULL不算重复）\n\n"
        "示例：\n"
        "CREATE TABLE example (\n"
        "  student_no VARCHAR(20) UNIQUE\n"
        ");\n\n"
        "或：ALTER TABLE example ADD UNIQUE (student_no);"
    ),
    'NOT_NULL': (
        "NOT NULL（非空）约束说明：\n\n"
        "非空约束确保列不能插入NULL值：\n\n"
        "示例：\n"
        "CREATE TABLE example (\n"
        "  student_name VARCHAR(50) NOT NULL\n"
        ");"
    ),
    'DEFAULT': (
        "DEFAULT（默认值）约束说明：\n\n"
        "默认值在插入数据未指定该列时自动填充：\n\n"
        "示例：\n"
        "CREATE TABLE example (\n"
        "  role VARCHAR(20) DEFAULT 'user'\n"
        ");"
    ),
    'BEGIN_COMMIT_ROLLBACK': (
        "事务控制语句说明：\n\n"
        "BEGIN / START TRANSACTION  -- 开始事务\n"
        "COMMIT   -- 提交事务，所有修改永久保存\n"
        "ROLLBACK -- 回滚事务，撤销所有未提交的修改\n\n"
        "示例：\n"
        "BEGIN;\n"
        "UPDATE account SET balance=balance-100 WHERE id=1;\n"
        "UPDATE account SET balance=balance+100 WHERE id=2;\n"
        "COMMIT;  -- 或 ROLLBACK; 撤销操作"
    ),
}

# DDL类关键词（需执行或返回SQL文本）
DDL_KEYWORDS = {
    'CREATE_DATABASE', 'DROP_DATABASE', 'CREATE_TABLE',
    'DROP_TABLE', 'ALTER_TABLE', 'COMMENT', 'ENGINE_CHARSET',
}

# DML类关键词（只返回SQL文本示例）
DML_KEYWORDS = {
    'INSERT', 'INSERT_MULTI', 'UPDATE', 'DELETE',
    'SELECT', 'FROM', 'WHERE',
}

# 事务约束类关键词（只返回SQL文本说明）
CONSTRAINT_KEYWORDS = {
    'PRIMARY_KEY', 'AUTO_INCREMENT', 'UNIQUE',
    'NOT_NULL', 'DEFAULT', 'BEGIN_COMMIT_ROLLBACK',
}

# 需要执行的DDL关键词
DDL_EXEC_KEYWORDS = {'DROP_DATABASE', 'DROP_TABLE', 'ALTER_TABLE'}

# 关键字详情映射
KEYWORD_INFO = {
    'CREATE_DATABASE': {'description': '创建student_manage数据库', 'executable': False, 'category': 'ddl'},
    'DROP_DATABASE': {'description': '删除数据库（危险操作）', 'executable': True, 'category': 'ddl'},
    'CREATE_TABLE': {'description': '创建学生信息表和用户表', 'executable': False, 'category': 'ddl'},
    'DROP_TABLE': {'description': '删除数据表（危险操作）', 'executable': True, 'category': 'ddl'},
    'ALTER_TABLE': {'description': '修改表结构，如新增字段', 'executable': True, 'category': 'ddl'},
    'COMMENT': {'description': '字段和表的注释说明', 'executable': False, 'category': 'ddl'},
    'ENGINE_CHARSET': {'description': '存储引擎和字符集配置', 'executable': False, 'category': 'ddl'},
    'INSERT': {'description': '单条插入学生数据', 'executable': False, 'category': 'dml'},
    'INSERT_MULTI': {'description': '多值批量插入（CSV导入）', 'executable': False, 'category': 'dml'},
    'UPDATE': {'description': '修改学生信息', 'executable': False, 'category': 'dml'},
    'DELETE': {'description': '删除学生数据', 'executable': False, 'category': 'dml'},
    'SELECT': {'description': '查询学生数据', 'executable': False, 'category': 'dml'},
    'FROM': {'description': '指定查询的数据表', 'executable': False, 'category': 'dml'},
    'WHERE': {'description': '条件筛选数据', 'executable': False, 'category': 'dml'},
    'PRIMARY_KEY': {'description': '主键约束，唯一标识每条记录', 'executable': False, 'category': 'constraint'},
    'AUTO_INCREMENT': {'description': '自增主键，自动生成递增ID', 'executable': False, 'category': 'constraint'},
    'UNIQUE': {'description': '唯一约束，确保字段值不重复', 'executable': False, 'category': 'constraint'},
    'NOT_NULL': {'description': '非空约束，确保必填字段不为空', 'executable': False, 'category': 'constraint'},
    'DEFAULT': {'description': '默认值约束，自动填充未指定的字段', 'executable': False, 'category': 'constraint'},
    'BEGIN_COMMIT_ROLLBACK': {'description': '事务控制，保证操作的原子性', 'executable': False, 'category': 'constraint'},
}

# 基础 JOIN SQL 片段，用于所有学生列表查询
STUDENT_JOIN_SQL = """
SELECT s.student_id, s.name, s.gender, s.birth_date, s.enrollment_year,
       s.status, s.phone, s.email, c.class_name, c.enrollment_year as class_year,
       m.major_name, d.dept_name
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id
LEFT JOIN majors m ON c.major_id = m.major_id
LEFT JOIN departments d ON m.dept_id = d.dept_id
"""

# 允许的字段名白名单（防止SQL注入，包含JOIN后的别名）
ALLOWED_FIELDS = {
    'student_id', 'name', 'gender', 'birth_date', 'enrollment_year',
    'status', 'phone', 'email', 'class_name', 'class_year',
    'major_name', 'dept_name'
}

# 允许的操作符白名单
ALLOWED_OPERATORS = {'=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN', 'NOT_IN', 'BETWEEN', 'IS_NULL', 'IS_NOT_NULL'}

# 统计场景SQL映射
STAT_SCENE_MAP = {
    'major_count': """
        SELECT m.major_name AS 专业, COUNT(*) AS 人数
        FROM students s
        JOIN classes c ON s.class_id = c.class_id
        JOIN majors m ON c.major_id = m.major_id
        GROUP BY m.major_name
    """,
    'grade_count': """
        SELECT c.enrollment_year AS 年级, COUNT(*) AS 人数
        FROM students s
        JOIN classes c ON s.class_id = c.class_id
        GROUP BY c.enrollment_year
    """,
    'class_count': """
        SELECT c.class_name AS 班级, COUNT(*) AS 人数
        FROM students s
        JOIN classes c ON s.class_id = c.class_id
        GROUP BY c.class_name
    """,
    'gender_count': """
        SELECT s.gender AS 性别, COUNT(*) AS 人数
        FROM students s
        GROUP BY s.gender
    """,
    'total_count': "SELECT COUNT(*) AS 总人数 FROM students",
    'dept_count': """
        SELECT d.dept_name AS 学院, COUNT(*) AS 人数
        FROM students s
        JOIN classes c ON s.class_id = c.class_id
        JOIN majors m ON c.major_id = m.major_id
        JOIN departments d ON m.dept_id = d.dept_id
        GROUP BY d.dept_name
    """,
    'distinct_major': "SELECT DISTINCT m.major_name AS 不重复专业 FROM majors m",
}


# 场景化查询配置
SCENE_QUERY_MAP = {
    'by_student_id': {
        'desc': '查询学号为 {val1} 的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE s.student_id = %s",
        'params': ['val1']
    },
    'by_name': {
        'desc': '查询姓名为 {val1} 的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE s.name = %s",
        'params': ['val1']
    },
    'by_major': {
        'desc': '查询 {val1} 专业的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE m.major_name = %s",
        'params': ['val1']
    },
    'by_dept': {
        'desc': '查询 {val1} 学院的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE d.dept_name = %s",
        'params': ['val1']
    },
    'by_enrollment_year': {
        'desc': '查询 {val1} 入学的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE s.enrollment_year = %s",
        'params': ['val1']
    },
    'by_gender': {
        'desc': '查询 {val1} 性别的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE s.gender = %s",
        'params': ['val1']
    },
    'by_class': {
        'desc': '查询 {val1} 班级的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE c.class_name = %s",
        'params': ['val1']
    },
    'by_name_like': {
        'desc': '查询姓名中包含 {val1} 的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE s.name LIKE %s",
        'params': ['val1']
    },
    'by_major_or': {
        'desc': '查询专业为 {val1} 或 {val2} 的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE m.major_name = %s OR m.major_name = %s",
        'params': ['val1', 'val2']
    },
    'by_not_major': {
        'desc': '查询非 {val1} 专业的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE m.major_name != %s",
        'params': ['val1']
    },
    'by_major_and_year': {
        'desc': '查询 {val1} 专业 {val2} 年入学的学生',
        'sql': STUDENT_JOIN_SQL + " WHERE m.major_name = %s AND s.enrollment_year = %s",
        'params': ['val1', 'val2']
    },
}


@app.route('/query')
def query_page():
    """高级查询页面"""
    tab = request.args.get('tab', 'condition')
    return render_template('query.html', active_tab=tab)


@app.route('/query/build', methods=['POST'])
def query_build():
    """动态条件查询构建"""
    data = request.get_json()
    conditions = data.get('conditions', [])
    do_export = data.get('export', False)

    if not conditions:
        return jsonify({'sql': '', 'columns': [], 'data': []})

    where_parts = []
    params = []

    for i, cond in enumerate(conditions):
        field = cond.get('field', '')
        operator = cond.get('operator', '')
        value = cond.get('value', '')
        value_to = cond.get('value_to', '')
        logic = cond.get('logic', 'AND')
        not_flag = cond.get('not', False)

        # 字段名白名单校验
        if field not in ALLOWED_FIELDS:
            return jsonify({'sql': '', 'columns': [], 'data': [], 'error': f'非法字段名: {field}'})

        # 操作符白名单校验
        if operator not in ALLOWED_OPERATORS:
            return jsonify({'sql': '', 'columns': [], 'data': [], 'error': f'非法操作符: {operator}'})

        # 构建条件片段
        not_prefix = 'NOT ' if not_flag else ''
        cond_str = ''
        if operator in ('=', '!=', '>', '<', '>=', '<='):
            cond_str = f"{field} {operator} %s"
            params.append(value)
        elif operator == 'LIKE':
            cond_str = f"{field} LIKE %s"
            params.append(value)
        elif operator == 'IN':
            values = [v.strip() for v in value.split(',') if v.strip()]
            placeholders = ','.join(['%s'] * len(values))
            cond_str = f"{field} IN ({placeholders})"
            params.extend(values)
        elif operator == 'NOT_IN':
            values = [v.strip() for v in value.split(',') if v.strip()]
            placeholders = ','.join(['%s'] * len(values))
            cond_str = f"{field} NOT IN ({placeholders})"
            params.extend(values)
        elif operator == 'BETWEEN':
            cond_str = f"{field} BETWEEN %s AND %s"
            params.append(value)
            params.append(value_to)
        elif operator == 'IS_NULL':
            cond_str = f"{field} IS NULL"
        elif operator == 'IS_NOT_NULL':
            cond_str = f"{field} IS NOT NULL"

        # 拼接NOT前缀和逻辑连接词
        part = f"{not_prefix}{cond_str}"
        if i == 0:
            where_parts.append(part)
        else:
            where_parts.append(f"{logic} {part}")

    where_clause = ' '.join(where_parts)
    sql = f"{STUDENT_JOIN_SQL} WHERE {where_clause}"

    # 如果需要导出CSV
    if do_export:
        csv_data = csv_handle.export_csv(sql, params or None)
        return send_file(csv_data, as_attachment=True, download_name='student_data.csv', mimetype='text/csv')

    try:
        rows = query(sql, params or None)
        columns = list(rows[0].keys()) if rows else []
        return jsonify({'sql': sql, 'columns': columns, 'data': rows})
    except Exception as e:
        return jsonify({'sql': sql, 'columns': [], 'data': []})


@app.route('/query/stat', methods=['POST'])
def query_stat():
    """统计查询"""
    data = request.get_json()
    scene = data.get('scene', '')

    sql = STAT_SCENE_MAP.get(scene)
    if sql is None:
        return jsonify({'sql': '', 'columns': [], 'data': []})

    try:
        rows = query(sql)
        columns = list(rows[0].keys()) if rows else []
        return jsonify({'sql': sql, 'columns': columns, 'data': rows})
    except Exception as e:
        return jsonify({'sql': sql, 'columns': [], 'data': []})


@app.route('/query/scene', methods=['POST'])
def query_scene():
    """场景化查询"""
    data = request.get_json()
    scene = data.get('scene', '')
    params = data.get('params', {})

    scene_config = SCENE_QUERY_MAP.get(scene)
    if scene_config is None:
        return jsonify({'sql': '', 'columns': [], 'data': [], 'desc': ''})

    # 构建参数列表
    param_values = []
    for p in scene_config['params']:
        val = params.get(p, '')
        if p == 'val1' and scene == 'by_name_like':
            val = f"%{val}%"
        param_values.append(val)

    sql = scene_config['sql']
    desc = scene_config['desc'].format(**params)
    
    # 处理导出
    if data.get('export', False):
        csv_data = csv_handle.export_csv(sql, param_values or None)
        return send_file(csv_data, as_attachment=True, download_name='scene_query_result.csv', mimetype='text/csv')

    try:
        rows = query(sql, param_values or None)
        columns = list(rows[0].keys()) if rows else []
        return jsonify({'sql': sql, 'columns': columns, 'data': rows, 'desc': desc})
    except Exception as e:
        return jsonify({'sql': sql, 'columns': [], 'data': [], 'desc': desc})


@app.route('/query/custom-sql', methods=['POST'])
def query_custom_sql():
    """执行自定义SQL查询语句"""
    data = request.get_json()
    sql = data.get('sql', '').strip()
    do_export = data.get('export', False)

    if not sql:
        return jsonify({'success': False, 'message': 'SQL语句不能为空'})

    # 安全检查：仅允许 SELECT 和 SHOW 语句
    sql_upper = sql.strip().upper()
    if not (sql_upper.startswith('SELECT') or sql_upper.startswith('SHOW')):
        return jsonify({'success': False, 'message': '仅允许执行 SELECT 和 SHOW 查询语句'})

    try:
        rows = query(sql)
        columns = list(rows[0].keys()) if rows else []

        if do_export:
            csv_data = csv_handle.export_csv(sql)
            return send_file(csv_data, as_attachment=True, download_name='custom_query_result.csv', mimetype='text/csv')

        return jsonify({
            'success': True,
            'sql': sql,
            'columns': columns,
            'data': rows
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'SQL执行错误：{str(e)}'})


@app.route('/query/sort', methods=['POST'])
def query_sort():
    """排序分页查询 - 支持多字段排序"""
    data = request.get_json()
    page = data.get('page', 1)

    # 支持新的多字段排序格式
    sort_fields = data.get('sort_fields', [])

    # 兼容旧格式
    if not sort_fields:
        sort_field = data.get('sort_field', 'student_no')
        sort_order = data.get('sort_order', 'asc')
        sort_field_2 = data.get('sort_field_2', '')
        sort_order_2 = data.get('sort_order_2', 'asc')

        if sort_field:
            sort_fields.append({'field': sort_field, 'order': sort_order})
        if sort_field_2:
            sort_fields.append({'field': sort_field_2, 'order': sort_order_2})

    # 如果没有排序字段，默认按学号排序
    if not sort_fields:
        sort_fields = [{'field': 'student_no', 'order': 'asc'}]

    # 字段名白名单校验和排序方向校验
    valid_sort_fields = []
    for sf in sort_fields:
        field = sf.get('field', '')
        order = sf.get('order', 'asc')
        if field in ALLOWED_FIELDS and order in ('asc', 'desc'):
            valid_sort_fields.append({'field': field, 'order': order})

    page_size = 10

    try:
        count_rows = query("SELECT COUNT(*) AS total FROM students")
        total = count_rows[0]['total'] if count_rows else 0
    except Exception:
        return jsonify({'sql': '', 'columns': [], 'data': [], 'total': 0, 'page': 1, 'total_pages': 0})

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    sql = STUDENT_JOIN_SQL

    # 构建 ORDER BY 子句
    if valid_sort_fields:
        order_parts = []
        for sf in valid_sort_fields:
            order_dir = 'ASC' if sf['order'] == 'asc' else 'DESC'
            order_parts.append(f"{sf['field']} {order_dir}")
        sql += " ORDER BY " + ", ".join(order_parts)

    offset = (page - 1) * page_size
    sql += f" LIMIT {page_size} OFFSET {offset}"

    try:
        rows = query(sql)
        columns = list(rows[0].keys()) if rows else []
        return jsonify({
            'sql': sql,
            'columns': columns,
            'data': rows,
            'total': total,
            'page': page,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'sql': sql, 'columns': [], 'data': [], 'total': total, 'page': page, 'total_pages': total_pages})


@app.route('/query/stat-with-params', methods=['POST'])
def query_stat_with_params():
    """带参数的统计查询 - 快捷操作功能"""
    data = request.get_json()
    action = data.get('action', '')
    params = data.get('params', {})

    base_sql = STUDENT_JOIN_SQL

    try:
        if action == 'major_count':
            # 专业人数统计，支持人数阈值
            threshold = int(params.get('threshold', 1))
            sql = f"""SELECT m.major_name AS 专业, COUNT(*) AS 人数
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id
LEFT JOIN majors m ON c.major_id = m.major_id
GROUP BY m.major_name
HAVING COUNT(*) >= {threshold}
ORDER BY 人数 DESC"""

        elif action == 'age_distribution':
            # 年龄分布统计
            ages_str = params.get('ages', '18,20,22')
            ages = [int(a.strip()) for a in ages_str.split(',') if a.strip().isdigit()]
            if not ages:
                ages = [18, 20, 22]

            case_parts = []
            prev_age = 0
            for age in sorted(ages):
                case_parts.append(f"SUM(CASE WHEN s.age < {age} AND s.age >= {prev_age} THEN 1 ELSE 0 END) AS '{prev_age}-{age}岁'")
                prev_age = age
            case_parts.append(f"SUM(CASE WHEN s.age >= {prev_age} THEN 1 ELSE 0 END) AS '{prev_age}岁以上'")

            sql = f"""SELECT
{',\n'.join(case_parts)}
FROM students s"""

        elif action == 'grade_count':
            # 年级人数统计
            sql = f"""SELECT c.grade AS 年级, COUNT(*) AS 人数
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id
GROUP BY c.grade
ORDER BY c.grade"""

        elif action == 'dept_count':
            # 学院人数统计
            sql = f"""SELECT d.dept_name AS 学院, COUNT(*) AS 人数
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id
LEFT JOIN majors m ON c.major_id = m.major_id
LEFT JOIN departments d ON m.dept_id = d.dept_id
GROUP BY d.dept_name
ORDER BY 人数 DESC"""

        elif action == 'custom_age_range':
            # 自定义年龄范围统计
            min_age = int(params.get('min_age', 18))
            max_age = int(params.get('max_age', 22))
            sql = f"""SELECT s.student_no AS 学号, s.student_name AS 姓名, s.age AS 年龄,
c.class_name AS 班级, c.grade AS 年级, m.major_name AS 专业, d.dept_name AS 学院
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id
LEFT JOIN majors m ON c.major_id = m.major_id
LEFT JOIN departments d ON m.dept_id = d.dept_id
WHERE s.age BETWEEN {min_age} AND {max_age}
ORDER BY s.age, s.student_no"""

        else:
            return jsonify({'sql': '', 'columns': [], 'data': [], 'error': '未知的统计类型'})

        rows = query(sql)
        columns = list(rows[0].keys()) if rows else []
        return jsonify({'sql': sql, 'columns': columns, 'data': rows})

    except Exception as e:
        return jsonify({'sql': '', 'columns': [], 'data': [], 'error': str(e)})


@app.route('/query/keyword')
def query_keyword():
    """查询关键字详情"""
    keyword = request.args.get('keyword', '')

    sql = SQL_MAP.get(keyword)
    if sql is None:
        return jsonify({'keyword': '', 'description': '', 'sql': '', 'executable': False, 'category': ''})

    info = KEYWORD_INFO.get(keyword, {'description': '', 'executable': False, 'category': ''})

    return jsonify({
        'keyword': keyword,
        'description': info['description'],
        'sql': sql,
        'executable': info['executable'],
        'category': info['category']
    })


@app.route('/query/keyword/execute', methods=['POST'])
def query_keyword_execute():
    """执行关键字对应的SQL（仅管理员）"""
    data = request.get_json()
    keyword = data.get('keyword', '')

    sql = SQL_MAP.get(keyword)
    if sql is None:
        return jsonify({'success': False, 'message': f'未找到关键字: {keyword}'})

    # 仅允许DDL_EXEC_KEYWORDS中的关键字执行
    if keyword not in DDL_EXEC_KEYWORDS:
        return jsonify({'success': False, 'message': f'关键字 {keyword} 不允许直接执行'})

    try:
        execute(sql)
        return jsonify({'success': True, 'message': '执行成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'执行失败：{e}'})


# ============================================
# 用户与权限管理API
# ============================================

@app.route('/user_management')
@permission_utils.require_admin()
def user_management_page():
    """用户管理页面"""
    return render_template('user_management.html')


@app.route('/user_management/permissions/<int:user_id>')
@permission_utils.require_admin()
def permission_management_page(user_id):
    """权限管理页面"""
    # 获取目标用户信息
    user = query(
        'SELECT user_id, uuid, username, role, ref_id, last_login, created_at FROM users WHERE user_id = %s',
        (user_id,)
    )
    if not user:
        return render_template('permission_management.html', target_user=None)
    return render_template('permission_management.html', target_user=user[0])


@app.route('/api/users', methods=['GET'])
@permission_utils.require_admin()
def api_users_list():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()

    base_sql = "SELECT user_id, uuid, username, role, ref_id, last_login, created_at FROM users WHERE 1=1"
    params = []
    
    if keyword:
        base_sql += " AND (username LIKE %s OR ref_id LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    base_sql += " ORDER BY created_at DESC"
    
    result = get_page_data(base_sql, page=page, page_size=page_size, params=params if params else None)
    return jsonify({
        'code': 0,
        'data': result['data'],
        'total': result['total'],
        'page': result['page'],
        'total_pages': result['total_pages']
    })


@app.route('/api/users', methods=['POST'])
@permission_utils.require_admin()
def api_create_user():
    """创建新用户"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'student').strip()
    ref_id = data.get('ref_id', '').strip()

    if not username or not password:
        return jsonify({'code': 1, 'msg': '用户名和密码不能为空'})
    
    if role not in ['admin', 'teacher', 'student']:
        role = 'student'

    try:
        user_uuid = permission_utils.generate_uuid()
        encrypted_password = password_utils.encrypt_password(password)
        execute(
            'INSERT INTO users(uuid, username, password_hash, role, ref_id) VALUES(%s, %s, %s, %s, %s)',
            (user_uuid, username, encrypted_password, role, ref_id or None)
        )
        permission_utils.initialize_user_permissions(user_uuid)
        return jsonify({'code': 0, 'msg': '创建成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '用户名已存在'})


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@permission_utils.require_admin()
def api_update_user(user_id):
    """更新用户信息"""
    data = request.get_json()
    username = data.get('username', '').strip()
    role = data.get('role', '').strip()
    ref_id = data.get('ref_id', '').strip()
    password = data.get('password', '').strip()

    update_fields = []
    params = []
    
    if username:
        update_fields.append('username = %s')
        params.append(username)
    if role and role in ['admin', 'teacher', 'student']:
        update_fields.append('role = %s')
        params.append(role)
    if ref_id:
        update_fields.append('ref_id = %s')
        params.append(ref_id)
    if password:
        encrypted_password = password_utils.encrypt_password(password)
        update_fields.append('password_hash = %s')
        params.append(encrypted_password)
    
    if not update_fields:
        return jsonify({'code': 1, 'msg': '没有需要更新的字段'})
    
    params.append(user_id)
    sql = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
    execute(sql, tuple(params))
    
    return jsonify({'code': 0, 'msg': '更新成功'})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@permission_utils.require_admin()
def api_delete_user(user_id):
    """删除用户"""
    if 'user_id' in session and session['user_id'] == user_id:
        return jsonify({'code': 1, 'msg': '不能删除自己的账号'})
    
    execute('DELETE FROM users WHERE user_id = %s', (user_id,))
    return jsonify({'code': 0, 'msg': '删除成功'})


@app.route('/api/users/<int:user_id>/permissions', methods=['GET'])
@permission_utils.require_admin()
def api_user_permissions(user_id):
    """获取用户权限"""
    user = query('SELECT uuid FROM users WHERE user_id = %s', (user_id,))
    if not user:
        return jsonify({'code': 1, 'msg': '用户不存在'})
    
    permissions = permission_utils.get_user_permissions(user[0]['uuid'])
    return jsonify({'code': 0, 'data': permissions})


@app.route('/api/users/<int:user_id>/permissions', methods=['PUT'])
@permission_utils.require_admin()
def api_set_user_permissions(user_id):
    """设置用户权限"""
    data = request.get_json()
    permissions_list = data.get('permissions', [])
    
    user = query('SELECT uuid FROM users WHERE user_id = %s', (user_id,))
    if not user:
        return jsonify({'code': 1, 'msg': '用户不存在'})
    
    user_uuid = user[0]['uuid']
    
    for perm in permissions_list:
        table_name = perm.get('table_name', '')
        perm_code = perm.get('permission_code', '000')
        permission_utils.set_user_permission(user_uuid, table_name, perm_code)
    
    return jsonify({'code': 0, 'msg': '权限设置成功'})


@app.route('/api/tables', methods=['GET'])
@permission_utils.require_admin()
def api_tables_list():
    """获取所有表名列表"""
    tables = [
        {'name': 'departments', 'label': '院系表'},
        {'name': 'majors', 'label': '专业表'},
        {'name': 'classes', 'label': '班级表'},
        {'name': 'students', 'label': '学生表'},
        {'name': 'teachers', 'label': '教师表'},
        {'name': 'courses', 'label': '课程表'},
        {'name': 'semesters', 'label': '学期表'},
        {'name': 'teaching', 'label': '授课安排表'},
        {'name': 'enrollments', 'label': '选课表'},
        {'name': 'grade_scale', 'label': '成绩等级表'},
        {'name': 'rewards_punishments', 'label': '奖惩表'},
        {'name': 'payments', 'label': '缴费表'},
        {'name': 'dorm_rooms', 'label': '宿舍表'},
        {'name': 'dorm_assignments', 'label': '住宿分配表'},
        {'name': 'curriculum', 'label': '培养计划表'},
        {'name': 'enroll_logs', 'label': '选课日志表'}
    ]
    return jsonify({'code': 0, 'data': tables})


if __name__ == '__main__':
    app.run(debug=True)
