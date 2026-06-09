# -*- coding: utf-8 -*-
"""测试配置 — PostgreSQL 连接管理（保持数据库复用）"""
import os, sys
from urllib.parse import urlparse

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

# 优先导入 bcrypt 以初始化 PyO3 运行时
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import pytest, dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

_TEST_DB_URL = None
_KEEP_DB = True

def pytest_addoption(parser):
    parser.addoption("--db-url", action="store", default=None, help="PostgreSQL 测试数据库 URL")
    parser.addoption("--no-keep-db", action="store_true", default=False, help="测试结束后删除数据库")

def _resolve_db_url(config) -> str:
    url = config.getoption("--db-url") or os.getenv("DATABASE_URL")
    if url:
        parsed = urlparse(url)
        db_name = parsed.path.lstrip("/")
        if db_name != "student_manage_test":
            from urllib.parse import urlunparse
            url = urlunparse(parsed._replace(path="/student_manage_test"))
    return url or "postgresql://postgres:114514@192.168.1.102:9527/student_manage_test"

def _terminate_connections(admin_url: str, db_name: str):
    import psycopg2
    try:
        conn = psycopg2.connect(admin_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()", (db_name,))
        cur.close(); conn.close()
    except Exception:
        pass

def _ensure_test_db(db_url: str):
    """仅当数据库不存在时创建"""
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/")
    admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
    _terminate_connections(admin_url, db_name)
    import psycopg2
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{db_name}" ENCODING "UTF8"')
        print(f"[DB] 创建数据库 {db_name}", flush=True)
    else:
        print(f"[DB] 数据库 {db_name} 已存在", flush=True)
    cur.close(); conn.close()

def _drop_test_db(db_url: str):
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/")
    admin_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
    _terminate_connections(admin_url, db_name)
    import psycopg2
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
    cur.close(); conn.close()

def pytest_sessionstart(session):
    global _TEST_DB_URL, _KEEP_DB
    _TEST_DB_URL = _resolve_db_url(session.config)
    _KEEP_DB = not session.config.getoption("--no-keep-db")
    os.environ["DATABASE_URL"] = _TEST_DB_URL
    try:
        from entity.base import engine
        engine.dispose()
        _ensure_test_db(_TEST_DB_URL)
        from entity.base import Base, engine
        import entity
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[WARN] 数据库初始化跳过 ({e})", flush=True)

def pytest_sessionfinish(session, exitstatus):
    if _TEST_DB_URL and not _KEEP_DB:
        try:
            _drop_test_db(_TEST_DB_URL)
        except Exception:
            pass

# ====== Fixtures ======

@pytest.fixture
def reset_tables():
    import entity
    from entity.base import Base, engine
    from sqlalchemy import text
    tables = ', '.join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
    if tables:
        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
            conn.commit()
    yield

@pytest.fixture
def client(reset_tables):
    from main import app
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "localhost"
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "admin"
        sess["user_role"] = "admin"
        sess["user_ref_id"] = "admin001"
        sess["user_uuid"] = "00000000-0000-0000-0000-000000000001"
        sess["username_changed"] = True
    return client

@pytest.fixture
def teacher_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["user_name"] = "teacher_test"
        sess["user_role"] = "teacher"
        sess["user_ref_id"] = "T001"
        sess["user_uuid"] = "00000000-0000-0000-0000-000000000002"
        sess["username_changed"] = True
    return client

@pytest.fixture
def student_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["user_name"] = "student_test"
        sess["user_role"] = "student"
        sess["user_ref_id"] = "S2024001"
        sess["user_uuid"] = "00000000-0000-0000-0000-000000000003"
        sess["username_changed"] = True
    return client

@pytest.fixture
def populated_db(auth_client):
    c = auth_client
    c.post("/api/departments", json={"dept_name": "计算机学院", "dean": "张教授", "phone": "010-12345678"})
    c.post("/api/majors", json={"major_name": "计算机科学与技术", "dept_id": 1, "duration": 4})
    c.post("/api/classes", json={"class_name": "计科1班", "major_id": 1, "enrollment_year": 2024})
    c.post("/api/teachers", json={"teacher_id": "T001", "name": "李教授", "gender": "M", "title": "教授"})
    c.post("/api/courses", json={"course_id": "CS101", "course_name": "数据结构", "credits": 4, "hours": 64, "type": "必修"})
    c.post("/api/semesters", json={"academic_year": "2024-2025", "semester_name": "第一学期", "start_date": "2024-09-01", "end_date": "2025-01-15"})
    return c

@pytest.fixture
def populated_db_full(auth_client):
    c = auth_client
    c.post("/api/departments", json={"dept_name": "计算机学院", "dean": "张教授", "phone": "010-12345678"})
    c.post("/api/majors", json={"major_name": "计算机科学与技术", "dept_id": 1, "duration": 4})
    c.post("/api/classes", json={"class_name": "计科1班", "major_id": 1, "enrollment_year": 2024})
    c.post("/add", data={"student_id": "2024001", "name": "张三", "gender": "M", "enrollment_year": "2024", "dept_id": "1", "class_id": "1"})
    c.post("/api/teachers", json={"teacher_id": "T001", "name": "李教授", "gender": "M", "title": "教授"})
    c.post("/api/courses", json={"course_id": "CS101", "course_name": "数据结构", "credits": 4, "hours": 64, "type": "必修"})
    c.post("/api/semesters", json={"academic_year": "2024-2025", "semester_name": "第一学期", "start_date": "2024-09-01", "end_date": "2025-01-15"})
    c.post("/api/teaching", json={"course_id": "CS101", "teacher_id": "T001", "semester_id": 1, "classroom": "A101", "schedule": "周一 1-2节", "capacity": 60})
    return c
