# -*- coding: utf-8 -*-
"""Middleware 单元测试 — auth_middleware"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import pytest
from flask import Flask, jsonify, session
from unittest.mock import patch


@pytest.fixture
def app():
    """创建最小 Flask 应用用于测试中间件"""
    _app = Flask(__name__)
    _app.secret_key = "test-secret"
    _app.config["TESTING"] = True
    _app.config["SERVER_NAME"] = "localhost"
    return _app


@pytest.fixture
def csrf_test_app():
    """用于 CSRF 测试的 Flask 应用（TESTING=False，让 CSRF 装饰器工作）"""
    _app = Flask(__name__)
    _app.secret_key = "test-secret"
    _app.config["TESTING"] = True
    _app.config["SERVER_NAME"] = "localhost"
    return _app


class TestRequireLogin:
    def test_with_session(self, app):
        from middleware.auth_middleware import require_login

        @app.route("/test")
        @require_login
        def view():
            return jsonify({"ok": True})

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
            resp = c.get("/test")
            assert resp.status_code == 200

    def test_without_session(self, app):
        from middleware.auth_middleware import require_login

        @app.route("/test")
        @require_login
        def view():
            return jsonify({"ok": True})

        with app.test_client() as c:
            resp = c.get("/test")
            assert resp.status_code == 401
            import json
            data = json.loads(resp.data)
            assert data["code"] == 1
            assert "登录" in data["msg"]


class TestRequireAdmin:
    def test_admin_allowed(self, app):
        from middleware.auth_middleware import require_admin

        @app.route("/test")
        @require_admin
        def view():
            return jsonify({"ok": True})

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
                sess["user_role"] = "admin"
            resp = c.get("/test")
            assert resp.status_code == 200

    def test_non_admin_denied(self, app):
        with patch("config.is_db_available", return_value=True):
            from middleware.auth_middleware import require_admin

            @app.route("/test")
            @require_admin
            def view():
                return jsonify({"ok": True})

            with app.test_client() as c:
                with c.session_transaction() as sess:
                    sess["user_id"] = 2
                    sess["user_role"] = "student"
                resp = c.get("/test")
                assert resp.status_code == 403
            import json
            data = json.loads(resp.data)
            assert "超級管理員" in data["msg"] or "超级管理员" in data["msg"]

    def test_no_session(self, app):
        from middleware.auth_middleware import require_admin

        @app.route("/test")
        @require_admin
        def view():
            return jsonify({"ok": True})

        with app.test_client() as c:
            resp = c.get("/test")
            assert resp.status_code == 401


class TestRequirePermission:
    def test_admin_bypass(self, app):
        from middleware.auth_middleware import require_permission, PERM_READ

        @app.route("/test")
        @require_permission("students", PERM_READ)
        def view():
            return jsonify({"ok": True})

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
                sess["user_role"] = "admin"
            resp = c.get("/test")
            assert resp.status_code == 200

    def test_no_session(self, app):
        from middleware.auth_middleware import require_permission, PERM_READ

        @app.route("/test")
        @require_permission("students", PERM_READ)
        def view():
            return jsonify({"ok": True})

        with app.test_client() as c:
            resp = c.get("/test")
            assert resp.status_code == 401


class TestCsrfProtect:
    """CSRF 保护装饰器测试
    注意：csrf_protect 在 TESTING=True 时会跳过验证，
    所以测试时需先设置 session（需要 TESTING=True），
    然后临时关闭 TESTING 让 CSRF 实际生效。
    """

    def _make_csrf_view(self, app):
        from middleware.auth_middleware import csrf_protect

        @app.route("/test", methods=["GET", "POST"])
        @csrf_protect
        def view():
            return jsonify({"ok": True})
        return view

    def test_get_bypasses_csrf(self, csrf_test_app):
        self._make_csrf_view(csrf_test_app)
        with csrf_test_app.test_client() as c:
            resp = c.get("/test")
            assert resp.status_code == 200

    def test_post_without_token(self, csrf_test_app):
        self._make_csrf_view(csrf_test_app)
        with csrf_test_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["_csrf_token"] = "valid-token"
            csrf_test_app.config["TESTING"] = False
            resp = c.post("/test")
            csrf_test_app.config["TESTING"] = True
            assert resp.status_code == 403

    def test_post_with_valid_token(self, csrf_test_app):
        self._make_csrf_view(csrf_test_app)
        with csrf_test_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["_csrf_token"] = "valid-token"
            csrf_test_app.config["TESTING"] = False
            resp = c.post("/test", headers={"X-CSRF-Token": "valid-token"})
            csrf_test_app.config["TESTING"] = True
            assert resp.status_code == 200

    def test_post_with_invalid_token(self, csrf_test_app):
        self._make_csrf_view(csrf_test_app)
        with csrf_test_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["_csrf_token"] = "real-token"
            csrf_test_app.config["TESTING"] = False
            resp = c.post("/test", headers={"X-CSRF-Token": "wrong-token"})
            csrf_test_app.config["TESTING"] = True
            assert resp.status_code == 403


class TestCSRFTokenGeneration:
    def test_generate_csrf_token(self, app):
        from middleware.auth_middleware import generate_csrf_token

        with app.test_request_context():
            token = generate_csrf_token()
            assert token is not None
            assert len(token) == 64  # 32 bytes hex = 64 chars

    def test_csrf_token_persistent(self, app):
        from middleware.auth_middleware import generate_csrf_token

        with app.test_request_context():
            t1 = generate_csrf_token()
            t2 = generate_csrf_token()
            assert t1 == t2  # 同一个 session 内 token 不变


class TestGlobalInterceptor:
    """测试全局拦截器（需用 main 中的 app，它有 register_global_interceptor）"""

    def test_white_list_bypass(self):
        from main import app as _app
        _app.config["TESTING"] = True
        with _app.test_client() as c:
            resp = c.get("/login")
            assert resp.status_code in (200, 302)

    def test_static_bypass(self):
        from main import app as _app
        _app.config["TESTING"] = True
        with _app.test_client() as c:
            resp = c.get("/static/css/style.css")
            assert resp.status_code != 401

    def test_api_no_session_returns_401_json(self):
        from main import app as _app
        _app.config["TESTING"] = True
        with _app.test_client() as c:
            resp = c.get("/api/students")
            assert resp.status_code == 401
            import json
            data = json.loads(resp.data)
            assert data["code"] == 1
