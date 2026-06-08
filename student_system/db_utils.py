"""
数据库操作工具模块，提供连接获取、查询、执行、分页等功能
"""

import math
import os

import pymysql

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


_db_initialized = False


def _ensure_db_initialized():
    """确保数据库和表已存在，不存在则执行init.sql初始化"""
    global _db_initialized
    if _db_initialized:
        return

    conn = None
    cursor = None
    try:
        # 先不指定database连接
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4',
            autocommit=True
        )
        cursor = conn.cursor()
        # 检查数据库是否存在
        cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (DB_NAME,))
        db_exists = cursor.fetchone() is not None

        need_init = False
        if not db_exists:
            need_init = True
        else:
            # 数据库已存在，检查新架构的 students 表是否存在
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'students'", (DB_NAME,))
            if cursor.fetchone() is None:
                need_init = True

        if need_init:
            sql_path = os.path.join(os.path.dirname(__file__), 'sql', 'init_complete.sql')
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            # 分割SQL语句并执行，跳过DELIMITER和触发器定义
            statements = []
            current_stmt = []
            in_trigger = False
            for line in sql_content.split('\n'):
                line_stripped = line.strip()
                # 跳过DELIMITER指令
                if line_stripped.upper().startswith('DELIMITER'):
                    continue
                # 检测触发器开始
                if 'CREATE TRIGGER' in line.upper():
                    in_trigger = True
                # 检测触发器结束
                if in_trigger and line_stripped == 'END//':
                    current_stmt.append('END')
                    in_trigger = False
                    continue
                if in_trigger and line_stripped == 'END':
                    current_stmt.append('END')
                    in_trigger = False
                    continue
                # 普通语句处理
                if not in_trigger:
                    if line_stripped and not line_stripped.startswith('--'):
                        current_stmt.append(line)
                    if line_stripped.endswith(';'):
                        stmt = '\n'.join(current_stmt).strip()
                        if stmt:
                            statements.append(stmt.rstrip(';'))
                        current_stmt = []
                else:
                    if line_stripped and not line_stripped.startswith('--'):
                        current_stmt.append(line)
            # 执行所有语句
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and len(stmt) > 5:
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        # 忽略已存在的错误
                        if 'already exists' not in str(e).lower():
                            print(f"SQL执行警告: {e}")

        _db_initialized = True
    except Exception as e:
        _db_initialized = False
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_conn():
    """获取数据库连接，失败时重置初始化状态并重试一次"""
    global _db_initialized
    _ensure_db_initialized()
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.err.OperationalError:
        # 数据库连接失败，重置初始化状态并重试
        _db_initialized = False
        _ensure_db_initialized()
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn


def query(sql, params=None):
    """执行SELECT查询，返回结果列表（字典格式）"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute(sql, params=None):
    """执行INSERT/UPDATE/DELETE，返回影响行数"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def build_filter_sql(filters, field_map):
    """
    根据筛选条件列表构建SQL WHERE子句和参数
    filters: list of dict [{"field":"dept_name", "op":"contains", "value":"计算机"}]
            op支持: eq, neq, contains, startswith, endswith, gt, gte, lt, lte, in, between
            in: value为逗号分隔的多值，e.g. "计算机,数学" → IN ('计算机','数学')
            between: value为逗号分隔的起止值，e.g. "18,25" → BETWEEN 18 AND 25
    field_map: dict mapping field names to SQL column expressions
               例: {"dept_name": "dept_name", "dept_id": "dept_id"}
    returns: (where_clause, params_list)
    """
    if not filters:
        return "", []

    clauses = []
    params = []

    for f in filters:
        field = f.get("field", "").strip()
        op = f.get("op", "eq").strip()
        value = f.get("value", "")

        # 跳过无效筛选条件
        if not field or field not in field_map:
            continue

        col = field_map[field]

        if op == "eq":
            clauses.append(f"AND {col} = %s")
            params.append(value)
        elif op == "neq":
            clauses.append(f"AND {col} != %s")
            params.append(value)
        elif op == "contains":
            clauses.append(f"AND {col} LIKE %s")
            params.append(f"%{value}%")
        elif op == "startswith":
            clauses.append(f"AND {col} LIKE %s")
            params.append(f"{value}%")
        elif op == "endswith":
            clauses.append(f"AND {col} LIKE %s")
            params.append(f"%{value}")
        elif op == "gt":
            clauses.append(f"AND {col} > %s")
            params.append(value)
        elif op == "gte":
            clauses.append(f"AND {col} >= %s")
            params.append(value)
        elif op == "lt":
            clauses.append(f"AND {col} < %s")
            params.append(value)
        elif op == "lte":
            clauses.append(f"AND {col} <= %s")
            params.append(value)
        elif op == "in":
            # 逗号分隔的多值筛选
            values = [v.strip() for v in value.split(",") if v.strip()]
            if values:
                placeholders = ", ".join(["%s"] * len(values))
                clauses.append(f"AND {col} IN ({placeholders})")
                params.extend(values)
        elif op == "between":
            # 逗号分隔的起止范围，如 "18,25"
            parts = [v.strip() for v in value.split(",", 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                clauses.append(f"AND {col} BETWEEN %s AND %s")
                params.extend([parts[0], parts[1]])

    return " ".join(clauses), params


def get_page_data(sql, page=1, page_size=10, params=None):
    """分页查询，返回分页信息及数据"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 查询总数
        count_sql = f"SELECT COUNT(*) AS total FROM ({sql}) AS t"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']

        # 计算总页数
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # 分页查询
        offset = (page - 1) * page_size
        page_sql = f"{sql} LIMIT %s OFFSET %s"
        page_params = list(params) if params else []
        page_params.extend([page_size, offset])
        cursor.execute(page_sql, page_params)
        data = cursor.fetchall()

        return {
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
