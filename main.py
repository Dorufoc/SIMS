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

def display_banner():
    subprocess.call('cls' if os.name == 'nt' else 'clear', shell=True)
    # 蓝绿紫渐变ANSI颜色代码
    GRADIENT = [
        '\033[94m',  # 蓝色
        '\033[96m',  # 青色
        '\033[92m',  # 绿色
        '\033[95m',  # 紫色
    ]
    RESET = '\033[0m'
    
    lines = [
        "                                           ",
        "                                           ",
        "                                           ",
        " .d8888b. 8888888 888b     d888  .d8888b.  ",
        "d88P  Y88b  888   8888b   d8888 d88P  Y88b ",
        "Y88b.       888   88888b.d88888 Y88b.      ",
        " \"Y888b.    888   888Y88888P888  \"Y888b.   ",
        "    \"Y88b.  888   888 Y888P 888     \"Y88b. ",
        "      \"888  888   888  Y8P  888       \"888 ",
        "Y88b  d88P  888   888   \"   888 Y88b  d88P ",
        " \"Y8888P\" 8888888 888       888  \"Y8888P\"  ",
        "                                           ",
        "                                           ",
        "                                           ",
    ]
    for i, line in enumerate(lines):
        color = GRADIENT[i % len(GRADIENT)]
        print(f"{color}{line}{RESET}")

def run_app(port=5000):
    """启动Flask Web应用"""
    from main import app
    from entity.base import init_db
    init_db()
    display_banner()
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
