"""
SQLAlchemy Base 和 Session 工厂
- 自动创建数据库（如不存在）
- 自动创建缺失的表
- 自动为已有表补充缺失的列、索引、唯一约束
"""
from urllib.parse import urlparse, urlunparse
from sqlalchemy import create_engine, inspect as sa_inspect, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect as pg_dialect
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_db():
    """获取数据库会话（依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
#  数据库 / 表 / 列 / 索引 / 约束 — 自动检测与补齐
# ============================================================

def _create_database_if_not_exists(target_url: str):
    """若目标数据库不存在，则自动创建（仅 PostgreSQL）"""
    parsed = urlparse(target_url)
    if parsed.scheme not in ('postgresql', 'postgres'):
        return

    db_name = parsed.path.lstrip('/')
    admin_url = urlunparse(parsed._replace(path='/postgres'))

    import psycopg2
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{db_name}" ENCODING \'UTF8\'')

    cur.close()
    conn.close()


def _is_postgresql() -> bool:
    """当前引擎是否为 PostgreSQL"""
    return engine.url.get_backend_name() in ('postgresql', 'postgres')


def _sync_all_metadata():
    """为已有表补充缺失的列、索引、唯一约束（仅 PostgreSQL）"""
    if not _is_postgresql():
        return

    pg = pg_dialect()
    inspector = sa_inspect(engine)
    changes = []

    for table_name, table in Base.metadata.tables.items():
        schema = table.schema or 'public'

        if not inspector.has_table(table_name, schema=schema):
            continue

        # ---- 1. 列 ----
        existing_cols = {c['name'] for c in inspector.get_columns(table_name, schema=schema)}
        for col_name, col in table.columns.items():
            if col_name in existing_cols:
                continue

            col_type_sql = col.type.compile(dialect=pg)
            default_sql = ''
            if col.server_default is not None:
                try:
                    default_sql = f' DEFAULT {col.server_default.arg.compile(dialect=pg)}'
                except Exception:
                    pass

            sql = f'ALTER TABLE {schema}."{table_name}" ADD COLUMN {col_name} {col_type_sql}{default_sql}'
            changes.append(('列', table_name, col_name, sql))

        # ---- 2. 索引 ----
        existing_idxs = {idx['name'] for idx in inspector.get_indexes(table_name, schema=schema)}
        for idx in table.indexes:
            if idx.name in existing_idxs:
                continue
            cols = ', '.join(c.name for c in idx.columns)
            unique = 'UNIQUE ' if idx.unique else ''
            sql = f'CREATE {unique}INDEX {idx.name} ON {schema}."{table_name}" ({cols})'
            changes.append(('索引', table_name, idx.name, sql))

        # ---- 3. UniqueConstraint ----
        existing_uqs = set()
        for uq in inspector.get_unique_constraints(table_name, schema=schema):
            existing_uqs.add(tuple(sorted(uq['column_names'])))

        for con in table.constraints:
            if not isinstance(con, UniqueConstraint):
                continue
            con_cols = tuple(sorted(c.name for c in con.columns))
            if con_cols in existing_uqs:
                continue
            col_list = ', '.join(c.name for c in con.columns)
            con_name = con.name or f'uk_{table_name}_{"_".join(c.name for c in con.columns)}'
            sql = f'ALTER TABLE {schema}."{table_name}" ADD CONSTRAINT {con_name} UNIQUE ({col_list})'
            changes.append(('唯一约束', table_name, con_name, sql))

    if not changes:
        return

    with engine.connect() as conn:
        for kind, tbl, obj, sql in changes:
            print(f'[DB Sync] + {kind}: {tbl}.{obj}')
            conn.execute(text(sql))
        conn.commit()

    print(f'[DB Sync] 同步完成，共 {len(changes)} 项变更')


def init_db():
    """初始化数据库：创建库 → 创建表 → 同步缺失的列/索引/约束"""
    _create_database_if_not_exists(DATABASE_URL)
    import entity  # noqa: F401 确保所有 Entity 已导入
    Base.metadata.create_all(bind=engine)
    _sync_all_metadata()
