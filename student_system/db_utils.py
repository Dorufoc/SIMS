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
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        # 检查数据库是否存在
        cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (DB_NAME,))
        if cursor.fetchone() is None:
            # 数据库不存在，执行init.sql
            sql_path = os.path.join(os.path.dirname(__file__), 'sql', 'init.sql')
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            # 按;分割逐条执行（跳过空语句）
            for stmt in sql_content.split(';'):
                stmt = stmt.strip()
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
        _db_initialized = True
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_conn():
    """获取数据库连接"""
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
