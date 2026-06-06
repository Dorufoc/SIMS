"""
学生信息管理系统 - Flask应用入口
提供用户认证、学生信息CRUD、CSV导入导出等功能
"""

from functools import wraps

import math
import pymysql

from flask import Flask, jsonify, redirect, render_template, request, send_file, session

from config import SECRET_KEY
import csv_handle
from db_utils import execute, get_page_data, query


app = Flask(__name__)
app.secret_key = SECRET_KEY


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
        'SELECT uid,username,role FROM user_info WHERE username=%s AND password=%s',
        (username, password)
    )

    if rows:
        user = rows[0]
        session['user_id'] = user['uid']
        session['user_name'] = user['username']
        session['user_role'] = user['role']
        return jsonify({'code': 0, 'msg': '登录成功'})
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

    try:
        execute(
            'INSERT INTO user_info(username,password,real_name) VALUES(%s,%s,%s)',
            (username, password, real_name)
        )
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


@app.route('/add', methods=['GET', 'POST'])
def add_student():
    """新增学生"""
    if request.method == 'GET':
        return render_template('add_stu.html')

    # 权限校验：仅管理员可新增
    if session.get('user_role') != 'admin':
        return jsonify({'code': 2, 'msg': '权限不足，仅管理员可执行此操作'})

    student_no = request.form.get('student_no', '').strip()
    student_name = request.form.get('student_name', '').strip()
    gender = request.form.get('gender', '').strip()
    age = request.form.get('age', '').strip()
    major = request.form.get('major', '').strip()
    grade = request.form.get('grade', '').strip()
    class_name = request.form.get('class_name', '').strip()

    try:
        execute(
            'INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name) VALUES(%s,%s,%s,%s,%s,%s,%s)',
            (student_no, student_name, gender, age, major, grade, class_name)
        )
        return jsonify({'code': 0, 'msg': '新增成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 1, 'msg': '学号已存在'})


@app.route('/manage')
def manage():
    """数据管理（分页展示）"""
    page = request.args.get('page', 1, type=int)
    page_data = get_page_data('SELECT * FROM student_info', page=page)
    return render_template(
        'manage.html',
        data=page_data['data'],
        page=page_data['page'],
        total_pages=page_data['total_pages']
    )


@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """编辑学生信息"""
    if request.method == 'GET':
        rows = query('SELECT * FROM student_info WHERE id=%s', (student_id,))
        return jsonify(rows[0]) if rows else jsonify({})

    # 权限校验：仅管理员可修改
    if session.get('user_role') != 'admin':
        return jsonify({'code': 2, 'msg': '权限不足，仅管理员可执行此操作'})

    student_name = request.form.get('student_name', '').strip()
    gender = request.form.get('gender', '').strip()
    age = request.form.get('age', '').strip()
    major = request.form.get('major', '').strip()
    grade = request.form.get('grade', '').strip()
    class_name = request.form.get('class_name', '').strip()

    execute(
        'UPDATE student_info SET student_name=%s,gender=%s,age=%s,major=%s,grade=%s,class_name=%s WHERE id=%s',
        (student_name, gender, age, major, grade, class_name, student_id)
    )
    return jsonify({'code': 0, 'msg': '修改成功'})


@app.route('/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """删除学生"""
    # 权限校验：仅管理员可删除
    if session.get('user_role') != 'admin':
        return jsonify({'code': 2, 'msg': '权限不足，仅管理员可执行此操作'})

    execute('DELETE FROM student_info WHERE id=%s', (student_id,))
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
    # 权限校验：仅管理员可导入
    if session.get('user_role') != 'admin':
        return jsonify({'code': 2, 'msg': '权限不足，仅管理员可执行此操作'})

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

# 允许的字段名白名单（防止SQL注入）
ALLOWED_FIELDS = {'student_no', 'student_name', 'gender', 'age', 'major', 'grade', 'class_name'}

# 允许的操作符白名单
ALLOWED_OPERATORS = {'=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN', 'NOT_IN', 'BETWEEN', 'IS_NULL', 'IS_NOT_NULL'}

# 统计场景SQL映射
STAT_SCENE_MAP = {
    'major_count': "SELECT major AS 专业, COUNT(*) AS 人数 FROM student_info GROUP BY major",
    'major_filter': "SELECT major AS 专业, COUNT(*) AS 人数 FROM student_info GROUP BY major HAVING COUNT(*)>1",
    'total_count': "SELECT COUNT(*) AS 总人数, COUNT(age) AS 有年龄数据人数 FROM student_info",
    'age_stats': "SELECT major AS 专业, AVG(age) AS 平均年龄, MAX(age) AS 最大年龄, MIN(age) AS 最小年龄, SUM(age) AS 年龄总和 FROM student_info GROUP BY major",
    'distinct_major': "SELECT DISTINCT major AS 不重复专业 FROM student_info",
}


@app.route('/query')
def query_page():
    """高级查询页面"""
    return render_template('query.html')


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
    sql = f"SELECT * FROM student_info WHERE {where_clause}"

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


@app.route('/query/sort', methods=['POST'])
def query_sort():
    """排序分页查询"""
    data = request.get_json()
    sort_field = data.get('sort_field', '')
    sort_order = data.get('sort_order', 'none')
    page = data.get('page', 1)

    # 字段名白名单校验
    if sort_field not in ALLOWED_FIELDS:
        return jsonify({'sql': '', 'columns': [], 'data': [], 'total': 0, 'page': 1, 'total_pages': 0})

    # 排序方向校验
    if sort_order not in ('asc', 'desc', 'none'):
        return jsonify({'sql': '', 'columns': [], 'data': [], 'total': 0, 'page': 1, 'total_pages': 0})

    page_size = 10

    # 查询总数
    try:
        count_rows = query("SELECT COUNT(*) AS total FROM student_info")
        total = count_rows[0]['total'] if count_rows else 0
    except Exception:
        return jsonify({'sql': '', 'columns': [], 'data': [], 'total': 0, 'page': 1, 'total_pages': 0})

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # 构建SQL
    sql = "SELECT * FROM student_info"
    if sort_order != 'none':
        order_dir = 'ASC' if sort_order == 'asc' else 'DESC'
        sql += f" ORDER BY {sort_field} {order_dir}"

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
    # 权限校验：仅管理员可执行
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足，仅管理员可执行此操作'})

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


if __name__ == '__main__':
    app.run(debug=True)
