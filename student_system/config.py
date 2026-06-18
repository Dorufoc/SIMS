"""
应用配置模块 - 从环境变量读取
启动时自动检测 .env 是否可用，不可用时自动回滚
"""
import os
import sys
import socket
from pathlib import Path
from dotenv import load_dotenv

# 全局 socket 超时：防止 psycopg2/pymysql 在 TCP 层面无限阻塞
socket.setdefaulttimeout(5)

# 路径常量
ENV_PATH = Path(__file__).resolve().parent / '.env'
ENV_BAK_PATH = Path(__file__).resolve().parent / '.env.bak'


def _test_db_connection(db_url: str) -> bool:
    """测试数据库是否可达。连接 postgres 默认库检查服务器是否存活，不依赖目标数据库是否存在。"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        if parsed.scheme.startswith('mysql'):
            import pymysql
            conn = pymysql.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username or 'root',
                password=parsed.password or '',
                database='mysql',
                connect_timeout=5,
            )
            conn.close()
        else:
            import psycopg2
            # 连接到 postgres 默认库而非目标数据库，避免因目标库不存在而误判
            test_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"
            conn = psycopg2.connect(test_url, connect_timeout=5)
            conn.close()
        return True
    except Exception:
        return False


def _rollback_env():
    """回滚 .env 文件：将 .env.bak 恢复为 .env"""
    if ENV_BAK_PATH.exists():
        import shutil
        shutil.copy2(ENV_BAK_PATH, ENV_PATH)
        # 删除备份文件，避免重复回滚
        ENV_BAK_PATH.unlink()
        return True
    return False


# ── 数据库可用性标志 ──
# True  = 数据库连接正常，全部功能可用
# False = 离线模式，仅允许本地管理员登录 + 设置页修改配置
_db_available = True


def is_db_available() -> bool:
    """返回当前数据库是否可用"""
    return _db_available


def set_db_available(available: bool):
    """外部（entity/base.py）在 init_db 后设置数据库可用性"""
    global _db_available
    _db_available = available


def _validate_and_rollback():
    """启动时验证 .env 中 DATABASE_URL 是否可用，不可用则自动回滚"""
    global _db_available

    if not ENV_PATH.exists():
        return

    load_dotenv(ENV_PATH)
    db_url = os.getenv('DATABASE_URL', '')

    if not db_url:
        # DATABASE_URL 为空，尝试回滚
        if _rollback_env():
            print('[配置] DATABASE_URL 为空，已自动回滚到上一个可用配置，请重启服务')
        else:
            print('[配置] DATABASE_URL 为空且无备份，服务将以离线模式启动')
            _db_available = False
        return

    if not _test_db_connection(db_url):
        print(f'[配置] 数据库连接失败 ({db_url})')
        if _rollback_env():
            print('[配置] 已自动回滚到上一个可用配置，请重启服务')
        else:
            print('[配置] 无备份文件可回滚，服务将以离线模式启动；登录仅支持默认管理员 admin/admin123')
            _db_available = False


# 启动时执行验证
_validate_and_rollback()

# 重新加载（可能已回滚）
load_dotenv(ENV_PATH)

FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# SECRET_KEY 校验：生产环境必须从环境变量设置
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if FLASK_ENV == 'production':
        raise RuntimeError('SECRET_KEY 环境变量未设置，生产环境必须提供 SECRET_KEY')
    SECRET_KEY = 'dev-secret-key'

# DATABASE_URL 校验：生产环境不允许硬编码回退值
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    if FLASK_ENV == 'production':
        raise RuntimeError('DATABASE_URL 环境变量未设置，生产环境必须提供 DATABASE_URL')
    DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/student_manage'

# 仪表盘模拟数据按钮开关（默认关闭）
SHOW_MOCK_DATA_BUTTON = os.getenv('SHOW_MOCK_DATA_BUTTON', 'false').lower() == 'true'

# 上传限制：最大 10MB
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB


def get_env_dynamic(key: str, default: str = '') -> str:
    """从 .env 文件实时读取某个键的值（不依赖缓存），用于运行时变更后立即生效"""
    if not ENV_PATH.exists():
        return default
    from dotenv import dotenv_values
    values = dotenv_values(ENV_PATH)
    return values.get(key, default)


def set_env_dynamic(key: str, value: str):
    """向 .env 文件写入或更新某个键值，运行时生效"""
    lines = []
    found = False
    if ENV_PATH.exists():
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    k, _ = stripped.split('=', 1)
                    if k.strip() == key:
                        lines.append(f'{key}={value}')
                        found = True
                        continue
                lines.append(line.rstrip('\n'))
    if not found:
        lines.append(f'{key}={value}')
    with open(ENV_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
