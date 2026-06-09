"""
学生信息管理系统 - Flask 应用入口 (MVC 重构版)
Flask 2.x + SQLAlchemy + PostgreSQL
前后端分离：后端只返回 JSON，前端通过 Ajax 调用
"""
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


if __name__ == '__main__':
    # 初始化数据库表
    init_db()
    app.run(debug=(FLASK_ENV == 'development'), host='0.0.0.0', port=5000)
