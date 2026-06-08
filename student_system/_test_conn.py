"""测试 PostgreSQL 连通性 - 最终版"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATABASE_URL
from urllib.parse import urlparse
import psycopg2

parsed = urlparse(DATABASE_URL)
masked = f'{parsed.scheme}://{parsed.username}:****@{parsed.hostname}:{parsed.port}/{parsed.path.lstrip("/")}'
print(f'目标: {masked}')

# 连接默认 postgres 库确认连通性
try:
    conn_str = f'postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres?connect_timeout=5'
    conn = psycopg2.connect(conn_str)
    print('连接 postgres 库成功!')
    cur = conn.cursor()
    
    # 检查 student_manage 是否存在
    cur.execute("SELECT datname FROM pg_database WHERE datname='student_manage'")
    if cur.fetchone():
        print('student_manage 数据库: 已存在')
    else:
        print('student_manage 数据库: 不存在，需要创建')
    
    cur.execute("SHOW server_encoding")
    print(f'服务端编码: {cur.fetchone()[0]}')
    
    cur.execute("SHOW lc_messages")
    print(f'lc_messages: {cur.fetchone()[0]}')
    
    conn.close()
except Exception as e:
    print(f'ERR: {e}')

# 再试 student_manage
print()
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print(f'student_manage 连接成功! Query: {result.fetchone()[0]}')
        
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
        tables = result.fetchall()
        print(f'表数量: {len(tables)}')
        for t in tables:
            print(f'  - {t[0]}')
except Exception as e:
    print(f'student_manage: {e}')
