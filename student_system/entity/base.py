"""
SQLAlchemy Base 和 Session 工厂
- 自动创建数据库（如不存在）
- 自动创建缺失的表
- 运行时懒修复：查询遇到表/列缺失时自动补齐并重试
"""
import hashlib
import json
import logging
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from sqlalchemy import create_engine, inspect as sa_inspect, text, UniqueConstraint
from sqlalchemy.pool import NullPool
from sqlalchemy.dialects.postgresql import dialect as pg_dialect
from sqlalchemy.exc import NoSuchTableError, ProgrammingError
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session, Session as _Session
from config import DATABASE_URL

_log = logging.getLogger('sqlalchemy')

try:
    from psycopg2 import errors as _pg_errors
    _SCHEMA_ERROR_CODES = frozenset(['42P01', '42703'])
except ImportError:
    _pg_errors = None
    _SCHEMA_ERROR_CODES = frozenset()


def _is_schema_error(exc: ProgrammingError) -> bool:
    orig = getattr(exc, 'orig', None)
    if orig is None or _pg_errors is None:
        return False
    pgcode = getattr(orig, 'pgcode', None)
    return pgcode in _SCHEMA_ERROR_CODES


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={'connect_timeout': 5},
)


class AutoRepairSession(_Session):
    """查询遇到表/列缺失时自动补齐 schema 并重试一次"""

    def execute(self, statement, params=None, **kw):
        try:
            return super().execute(statement, params, **kw)
        except ProgrammingError as e:
            if not _is_schema_error(e):
                raise
            _log.warning('[AutoRepair] 检测到 schema 缺失，自动补齐: %s', e.orig)
            try:
                _sync_all_metadata(force=True)
            except Exception as repair_err:
                _log.error('[AutoRepair] 自动修复失败: %s', repair_err)
            try:
                self.rollback()
            except Exception:
                pass
            return super().execute(statement, params, **kw)


SessionLocal = scoped_session(
    sessionmaker(class_=AutoRepairSession, autocommit=False, autoflush=False, bind=engine)
)


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
    """若目标数据库不存在，则自动创建（仅 PostgreSQL）
    
    连接失败时不阻塞启动 —— 数据库可能已存在，后续 create_all 会自行处理。
    """
    parsed = urlparse(target_url)
    if parsed.scheme not in ('postgresql', 'postgres'):
        return

    db_name = parsed.path.lstrip('/')
    admin_url = urlunparse(parsed._replace(path='/postgres'))

    try:
        import psycopg2
        conn = psycopg2.connect(admin_url, connect_timeout=5)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{db_name}" ENCODING \'UTF8\'')

        cur.close()
        conn.close()
    except Exception as e:
        print(f'[DB] 数据库自动创建跳过（{e}）')


def _is_postgresql() -> bool:
    """当前引擎是否为 PostgreSQL"""
    return engine.url.get_backend_name() in ('postgresql', 'postgres')


_SCHEMA_CACHE_FILE = Path(__file__).resolve().parent / '.schema_cache'


def _build_schema_hash() -> str:
    """根据当前 metadata 构建 schema 指纹，用于判断是否需要重新同步"""
    tables_info: dict = {}
    for table_name, table in sorted(Base.metadata.tables.items()):
        cols = sorted(f"{c.name}:{c.type}" for c in table.columns)
        idxs = sorted(f"{idx.name}:{','.join(c.name for c in idx.columns)}:unique={idx.unique}"
                      for idx in table.indexes)
        uqs = sorted(
            f"uq:{','.join(sorted(c.name for c in con.columns))}"
            for con in table.constraints if isinstance(con, UniqueConstraint)
        )
        tables_info[table_name] = cols + ['@idx'] + idxs + ['@uq'] + uqs
    payload = json.dumps(tables_info, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def _sync_all_metadata(force: bool = False):
    """为已有表补充缺失的列、索引、唯一约束（仅 PostgreSQL）

    force=True 时跳过缓存直接全量同步（用于运行时懒修复）。
    schema 未变更时跳过检查，避免每次启动/重载都全量扫描数据库。
    """
    if not _is_postgresql():
        return

    current_hash = _build_schema_hash()

    if not force:
        cached = ''
        if _SCHEMA_CACHE_FILE.exists():
            cached = _SCHEMA_CACHE_FILE.read_text().strip()
        if cached == current_hash:
            sample_table = sorted(Base.metadata.tables.keys())[0] if Base.metadata.tables else None
            if sample_table:
                try:
                    with engine.connect() as conn:
                        schema = Base.metadata.tables[sample_table].schema or 'public'
                        result = conn.execute(text(
                            "SELECT EXISTS (SELECT FROM information_schema.tables "
                            "WHERE table_schema = :schema AND table_name = :tbl)"
                        ), {'schema': schema, 'tbl': sample_table})
                        if result.scalar():
                            return
                except Exception:
                    pass

    pg = pg_dialect()
    inspector = sa_inspect(engine)
    changes = []

    for table_name, table in Base.metadata.tables.items():
        schema = table.schema or 'public'

        if not inspector.has_table(table_name, schema=schema):
            continue

        # ---- 1. 列 ----
        try:
            existing_cols = {c['name'] for c in inspector.get_columns(table_name, schema=schema)}
        except NoSuchTableError:
            continue
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

    # 无论是否有变更，都更新缓存（确保 schema hash 与数据库实际状态一致）
    try:
        _SCHEMA_CACHE_FILE.write_text(current_hash)
    except OSError:
        pass

    if not changes:
        return

    with engine.connect() as conn:
        for kind, tbl, obj, sql in changes:
            print(f'[DB Sync] + {kind}: {tbl}.{obj}')
            conn.execute(text(sql))
        conn.commit()

    print(f'[DB Sync] 同步完成，共 {len(changes)} 项变更')


def _seed_default_admin():
    """插入默认管理员账号，仅在首次创建时设置默认密码。"""
    from utils.password_utils import encrypt_password

    with SessionLocal() as db:
        from entity.user import User

        DEFAULT_PASSWORD = 'admin'

        existing = db.query(User).filter(User.username == 'admin').first()
        if existing:
            # 已存在则不重置密码
            print('[DB] 默认管理员已存在，跳过密码重置')
            return

        admin = User(
            uuid='00000000-0000-0000-0000-000000000001',
            username='admin',
            password_hash=encrypt_password(DEFAULT_PASSWORD),
            role='admin',
            username_changed=True,
        )
        db.add(admin)
        db.commit()
        print('[DB] 默认管理员已创建 (admin/admin)')


def init_db():
    """初始化数据库：创建库 → 创建表 → 种子数据 → 增量补齐

    schema 一致时近乎零开销（缓存命中后仅一条轻量查询）。
    列/索引/约束缺失时自动补齐，运行时首次查询遇到缺失也会自动修复。
    失败时不会阻塞启动，而是将数据库标记为不可用（离线模式）。
    """
    from config import set_db_available, is_db_available

    if not is_db_available():
        print('[DB] 数据库已被标记为不可用，跳过初始化（离线模式）')
        return

    try:
        _create_database_if_not_exists(DATABASE_URL)
        import entity  # noqa: F401 确保所有 Entity 已导入
        Base.metadata.create_all(bind=engine)
        _seed_default_admin()
        _sync_all_metadata()  # schema 一致时瞬间跳过（cache），变更时补齐
        set_db_available(True)
        print('[DB] 数据库初始化成功')
    except Exception as e:
        set_db_available(False)
        print(f'[DB] 数据库初始化失败，服务进入离线模式: {e}')
