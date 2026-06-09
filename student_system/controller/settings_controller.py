"""系统设置 API"""
import os
import sys
import time
import subprocess
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qs
from flask import Blueprint, request, jsonify, render_template
from middleware.auth_middleware import require_admin, csrf_protect

settings_bp = Blueprint('settings', __name__)

# .env 路径（config.py 同目录）
ENV_PATH = Path(__file__).resolve().parent.parent / '.env'
ENV_BAK_PATH = Path(__file__).resolve().parent.parent / '.env.bak'


@settings_bp.route('/settings')
@require_admin
def settings_page():
    """设置页面"""
    return render_template('settings.html')


def _parse_database_url(url: str) -> dict:
    """将 DATABASE_URL 解析为各组件"""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': str(parsed.port or 5432),
        'username': parsed.username or 'postgres',
        'password': parsed.password or '',
        'database': parsed.path.lstrip('/') or 'student_manage',
    }


def _build_database_url(host: str, port: str, username: str, password: str, database: str) -> str:
    """根据组件构建 DATABASE_URL"""
    # 处理密码中的特殊字符，使用 URL 编码
    from urllib.parse import quote
    encoded_password = quote(password, safe='')
    return f'postgresql://{username}:{encoded_password}@{host}:{port}/{database}'


def _test_database_connection(url: str) -> tuple:
    """测试数据库连接（自动识别 MySQL / PostgreSQL），返回 (success: bool, error_msg: str)"""
    try:
        parsed = urlparse(url)
        if parsed.scheme.startswith('mysql'):
            import pymysql
            conn = pymysql.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username or 'root',
                password=parsed.password or '',
                database=parsed.path.lstrip('/'),
                connect_timeout=5,
            )
            conn.close()
        else:
            import psycopg2
            conn = psycopg2.connect(url, connect_timeout=5)
            conn.close()
        return True, ''
    except Exception as e:
        return False, str(e)


def _read_env() -> dict:
    """读取 .env 文件内容"""
    env_vars = {}
    if ENV_PATH.exists():
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def _write_env(env_vars: dict):
    """写入 .env 文件"""
    lines = []
    for key, value in env_vars.items():
        lines.append(f'{key}={value}')
    with open(ENV_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def _restart_server():
    """重启服务器（在新进程中启动，当前进程退出）"""
    # 根目录 main.py 路径
    root_main = Path(__file__).resolve().parent.parent.parent / 'main.py'

    # 获取当前启动参数
    args = sys.argv[1:] if len(sys.argv) > 1 else ['run']

    # 使用 subprocess 启动新进程
    python_exe = sys.executable
    subprocess.Popen(
        [python_exe, str(root_main)] + args,
        cwd=str(root_main.parent),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
    )

    # 延迟一下让新进程启动，然后退出当前进程
    def shutdown():
        time.sleep(0.5)
        os._exit(0)

    # 在另一个线程中执行退出，让当前请求能正常返回
    import threading
    t = threading.Thread(target=shutdown)
    t.daemon = True
    t.start()


@settings_bp.route('/api/settings/database', methods=['GET'])
@require_admin
def api_get_database_config():
    """获取当前数据库配置（离线模式下返回全空，避免泄露 ENV 敏感信息）"""
    from config import is_db_available
    # 离线模式：返回空配置，用户需手动填写，防止泄露 .env 中的密码等信息
    if not is_db_available():
        return jsonify({'code': 0, 'data': {
            'host': '', 'port': '', 'username': '', 'password': '', 'database': ''
        }})

    env_vars = _read_env()
    db_url = env_vars.get('DATABASE_URL', '')
    if db_url:
        config = _parse_database_url(db_url)
        # 密码字段返回掩码，不暴露明文
        if config.get('password'):
            config['password'] = '******'
    else:
        config = {'host': '', 'port': '', 'username': '', 'password': '', 'database': ''}
    return jsonify({'code': 0, 'data': config})


@settings_bp.route('/api/settings/database', methods=['POST'])
@require_admin
@csrf_protect
def api_update_database_config():
    """更新数据库配置并重启"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 1, 'msg': '参数不能为空'})

    host = data.get('host', '').strip()
    port = data.get('port', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    database = data.get('database', '').strip()

    # 验证必填字段
    if not all([host, port, username, database]):
        return jsonify({'code': 1, 'msg': '服务器地址、端口、账号、基础数据库为必填项'})

    # 验证端口是数字
    try:
        int(port)
    except ValueError:
        return jsonify({'code': 1, 'msg': '端口必须是数字'})

    # 构建新的 DATABASE_URL
    new_url = _build_database_url(host, port, username, password, database)

    # 测试新连接是否可用
    success, error_msg = _test_database_connection(new_url)
    if not success:
        return jsonify({'code': 1, 'msg': f'数据库连接测试失败：{error_msg}'})

    # 备份当前 .env
    env_vars = _read_env()
    old_db_url = env_vars.get('DATABASE_URL', '')

    # 写入新配置
    env_vars['DATABASE_URL'] = new_url

    # 先备份旧 .env（如果存在）
    if ENV_PATH.exists():
        import shutil
        shutil.copy2(ENV_PATH, ENV_BAK_PATH)

    _write_env(env_vars)

    # 返回成功，提示用户确认重启
    return jsonify({'code': 0, 'msg': '配置已保存，服务器即将重启...', 'restart': True})


@settings_bp.route('/api/settings/database/test', methods=['POST'])
@require_admin
@csrf_protect
def api_test_database_config():
    """仅测试数据库连接，不保存配置"""
    data = request.get_json()
    if not data:
        return jsonify({'code': 1, 'msg': '参数不能为空'})

    host = data.get('host', '').strip()
    port = data.get('port', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    database = data.get('database', '').strip()

    if not all([host, port, username, database]):
        return jsonify({'code': 1, 'msg': '请填写完整的数据库连接信息'})

    try:
        int(port)
    except ValueError:
        return jsonify({'code': 1, 'msg': '端口必须是数字'})

    new_url = _build_database_url(host, port, username, password, database)
    success, error_msg = _test_database_connection(new_url)

    if success:
        return jsonify({'code': 0, 'msg': '数据库连接测试成功！'})
    else:
        return jsonify({'code': 1, 'msg': f'数据库连接测试失败：{error_msg}'})


@settings_bp.route('/api/settings/restart', methods=['POST'])
@require_admin
@csrf_protect
def api_restart_server():
    """手动重启服务器"""
    _restart_server()
    return jsonify({'code': 0, 'msg': '服务器正在重启...'})


@settings_bp.route('/api/settings/mock-data-toggle', methods=['GET'])
@require_admin
def api_get_mock_data_toggle():
    """获取模拟数据按钮开关状态"""
    from config import get_env_dynamic
    enabled = get_env_dynamic('SHOW_MOCK_DATA_BUTTON', 'false').lower() == 'true'
    return jsonify({'code': 0, 'data': {'enabled': enabled}})


@settings_bp.route('/api/settings/mock-data-toggle', methods=['POST'])
@require_admin
@csrf_protect
def api_set_mock_data_toggle():
    """设置模拟数据按钮开关状态"""
    data = request.get_json()
    if data is None:
        return jsonify({'code': 1, 'msg': '参数不能为空'})

    enabled = data.get('enabled', False)
    value = 'true' if enabled else 'false'

    from config import set_env_dynamic
    set_env_dynamic('SHOW_MOCK_DATA_BUTTON', value)

    status = '已开启' if enabled else '已关闭'
    return jsonify({'code': 0, 'msg': f'模拟数据按钮{status}，刷新仪表盘即可生效'})
