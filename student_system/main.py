"""
学生信息管理系统 - Flask 应用入口 (MVC 重构版)
Flask 2.x + SQLAlchemy + PostgreSQL
前后端分离：后端只返回 JSON，前端通过 Ajax 调用

用法:
  python student_system/main.py              启动Web应用（默认端口5000）
  python student_system/main.py run          启动Web应用
  python student_system/main.py run -p 8080  指定端口启动
  python student_system/main.py test         运行全部测试
"""
import sys
import os
import subprocess

from flask import Flask, jsonify
from config import SECRET_KEY, FLASK_ENV, MAX_CONTENT_LENGTH
from entity.base import init_db
from controller import register_all
from middleware.auth_middleware import register_global_interceptor


def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.debug = (FLASK_ENV == 'development')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    if FLASK_ENV == 'production':
        app.config['SESSION_COOKIE_SECURE'] = True

    # 注入离线模式标志到模板全局变量
    from config import is_db_available
    app.jinja_env.globals['offline_mode'] = not is_db_available()

    # 注册全局登录拦截器
    register_global_interceptor(app)

    # 注册所有 API Blueprint
    register_all(app)

    # 安全响应头
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    # 错误处理
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'code': 404, 'msg': '资源不存在'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

    return app


app = create_app()


def display_banner():
    # subprocess.call('cls' if os.name == 'nt' else 'clear', shell=True)
    # 纯黄色ANSI颜色代码
    GRADIENT = [
        '\033[93m',          # 黄色
    ]
    RESET = '\033[0m'

    lines = [

        "      @@@@@@@@@@   @@@@@@@    @@@@@@@      ",
        "     @@@@@@@@@@@@ @@@@@@@    @@@@@@@       ",
        "    @@@@@@@@@@@@@@@@@@@@    @@@@@@@        ",
        "            @@@@@@@@@@@    @@@@@@@         ",
        "             @@@@@@@@@    @@@@@@@          ",
        "              @@@@@@@    @@@@@@@           ",
        "               @@@@@@@  @@@@@@@            ",
        "                @@@@@@bd@@@@@@             ",
        "                 @@@@@@@@@@@@              ",
        "                  @@@@@@@@@@               ",
        "                   @@@@@@@@                ",
        "                    @@@@@@                 ",
        "                     @@@@                  ",
        "                                             ",
        " .d8888b.  8888888 888b     d888  .d8888b.  ",
        "d88P  Y88b   888   8888b   d8888 d88P  Y88b ",
        "Y88b.        888   88888b.d88888 Y88b.      ",
        " \"Y888b.     888   888Y88888P888  \"Y888b.  ",
        "    \"Y88b.   888   888 Y888P 888     \"Y88b.",
        "      \"888   888   888  Y8P  888       \"888",
        "Y88b  d88P   888   888   \"   888 Y88b  d88P ",
        " \"Y8888P\"  8888888 888       888  \"Y8888P\"",
        "                                             ",
        " CIVIL AVIATION FLIGHT UNIVERSITY OF CHINA  ",
        "      STUDENT INFO MANAGEMENT SYSTEM        ",
        "                                             ",
    ]
    for i, line in enumerate(lines):
        color = GRADIENT[i % len(GRADIENT)]
        print(f"{color}{line}{RESET}")


def run_app(port=5000):
    """启动Flask Web应用"""
    # 先显示字符画和加载提示
    display_banner()
    print("系统加载中...\n")

    init_db()

    # 初始化完成，清屏重新显示完整信息
    subprocess.call('cls' if os.name == 'nt' else 'clear', shell=True)
    display_banner()
    print(f"[OK] 系统启动完成！\n")
    print(f"项目访问地址: http://127.0.0.1:{port}")
    print(f"按 Ctrl+C 停止服务")
    app.run(host='0.0.0.0', port=port, debug=(FLASK_ENV == 'development'))


def run_tests():
    """运行全部测试"""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'),
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
