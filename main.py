"""
学生信息管理系统 - 全局启动入口
用法:
  python main.py              启动Web应用（默认端口5000）
  python main.py run          启动Web应用
  python main.py run -p 8080  指定端口启动
  python main.py test         运行全部测试
"""

import sys
import os
import subprocess

# 将 student_system 目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'student_system'))

# ── 启动前先验证 .env 配置有效性 ──
# 注意：每个进程独立验证一次（包括重启后的新进程）
_env_validated = False


def validate_env():
    """独立进程启动时验证 .env 配置，失败则自动回滚（不再退出，允许离线模式）"""
    global _env_validated
    if _env_validated:
        return
    _env_validated = True

    from pathlib import Path
    from dotenv import load_dotenv
    import os as _os

    env_path = Path(__file__).resolve().parent / 'student_system' / '.env'
    env_bak = Path(__file__).resolve().parent / 'student_system' / '.env.bak'

    if not env_path.exists():
        return

    load_dotenv(env_path)
    db_url = _os.getenv('DATABASE_URL', '')

    if not db_url:
        rollback_env(env_path, env_bak, exit_on_fail=False)
        return

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
                database=parsed.path.lstrip('/'),
                connect_timeout=5,
            )
            conn.close()
        else:
            import psycopg2
            conn = psycopg2.connect(db_url, connect_timeout=5)
            conn.close()
    except Exception as e:
        print(f'[启动检查] 数据库连接失败: {e}')
        rollback_env(env_path, env_bak, exit_on_fail=False)


def rollback_env(env_path, env_bak, exit_on_fail=True):
    """回滚 .env（可选是否退出进程）"""
    import shutil
    if env_bak.exists():
        shutil.copy2(env_bak, env_path)
        env_bak.unlink()
        print('[启动检查] 配置已自动回滚到上一个可用版本，请重新启动应用')
        if exit_on_fail:
            sys.exit(1)
    else:
        print('[启动检查] 数据库连接失败且无备份可回滚，将以离线模式启动')
        if exit_on_fail:
            sys.exit(1)


def display_banner():
    # subprocess.call('cls' if os.name == 'nt' else 'clear', shell=True)
    # 纯黄色ANSI颜色代码
    GRADIENT = [
        '\033[93m',          # 黄色
    ]
    RESET = '\033[0m'

    lines = [


        "     @@@@@@@@@@   @@@@@@@    @@@@@@@      ",
        "    @@@@@@@@@@@@ @@@@@@@    @@@@@@@       ",
        "   @@@@@@@@@@@@@@@@@@@@    @@@@@@@        ",
        "           @@@@@@@@@@@    @@@@@@@         ",
        "            @@@@@@@@@    @@@@@@@          ",
        "             @@@@@@@    @@@@@@@           ",
        "              @@@@@@@  @@@@@@@            ",
        "               @@@@@@bd@@@@@@             ",
        "                @@@@@@@@@@@@              ",
        "                 @@@@@@@@@@               ",
        "                  @@@@@@@@                ",
        "                   @@@@@@                 ",
        "                    @@@@                  ",
        "                                          ",
        " .d8888b. 8888888 888b     d888  .d8888b.  ",
        "d88P  Y88b  888   8888b   d8888 d88P  Y88b ",
        "Y88b.       888   88888b.d88888 Y88b.      ",
        " \"Y888b.    888   888Y88888P888  \"Y888b.   ",
        "    \"Y88b.  888   888 Y888P 888     \"Y88b. ",
        "      \"888  888   888  Y8P  888       \"888 ",
        "Y88b  d88P  888   888   \"   888 Y88b  d88P ",
        " \"Y8888P\" 8888888 888       888  \"Y8888P\"  ",
        "                                           ",
        " CIVIL AVIATION FLIGHT UNIVERSITY OF CHINA ",
        "      STUDENT INFO MANAGEMENT SYSTEM       ",
        "                                           ",
    ]
    for i, line in enumerate(lines):
        color = GRADIENT[i % len(GRADIENT)]
        print(f"{color}{line}{RESET}")


def run_app(port=5000):
    """启动Flask Web应用"""
    # 先显示字符画和加载提示
    display_banner()
    print("系统加载中...\n")

    from main import app
    from entity.base import init_db
    init_db()

    # 初始化完成，清屏重新显示完整信息
    subprocess.call('cls' if os.name == 'nt' else 'clear', shell=True)
    display_banner()
    print(f"[✓] 系统启动完成！\n")
    print(f"项目访问地址: http://127.0.0.1:{port}")
    print(f"按 Ctrl+C 停止服务")
    app.run(host='0.0.0.0', port=port, debug=(os.getenv('FLASK_ENV', 'development') == 'development'))


def run_tests():
    """运行全部测试"""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'student_system', 'tests'),
        pattern='test_*.py'
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


def print_usage():
    """打印使用说明"""
    print(__doc__)


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args or args[0] == 'run':
        port = 5000
        if '-p' in args:
            try:
                port = int(args[args.index('-p') + 1])
            except (IndexError, ValueError):
                print("错误: -p 参数后需指定端口号")
                sys.exit(1)
        run_app(port)
    elif args[0] == 'test':
        run_tests()
    else:
        print_usage()
