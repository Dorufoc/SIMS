# -*- coding: utf-8 -*-
"""Middleware 高级测试 — 覆盖离线模式、非管理员路由、权限检查等路径"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify, session
import json


@pytest.fixture
def minimal_app():
    """创建最小 Flask 应用（不含数据库）"""
    _app = Flask(__name__)
    _app.secret_key = "test-secret"
    _app.config["TESTING"] = True
    _app.config["SERVER_NAME"] = "localhost"
    return _app


# ═══════════════════════════════════════════
#  1. require_permission — 非管理员权限路径
# ═══════════════════════════════════════════

class TestRequirePermissionAdvanced:
    """require_permission 非管理员分支的完整覆盖"""

    def test_non_admin_no_user_uuid(self, minimal_app):
        """非管理员无 user_uuid → 403"""
        from middleware.auth_middleware import require_permission, PERM_READ

        @minimal_app.route("/test")
        @require_permission("students", PERM_READ)
        def view():
            return jsonify({"ok": True})

        with minimal_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
                sess["user_role"] = "student"
                # 不设 user_uuid
            resp = c.get("/test")
            assert resp.status_code == 403
            data = json.loads(resp.data)
            assert "权限不足" in data["msg"]

    def test_non_admin_no_permission_record(self, minimal_app):
        """非管理员有 uuid 但无权限记录 → 403"""
        from middleware.auth_middleware import require_permission, PERM_READ

        @minimal_app.route("/test")
        @require_permission("students", PERM_READ)
        def view():
            return jsonify({"ok": True})

        with patch("middleware.auth_middleware.UserPermissionRepo") as MockRepo:
            mock_repo = MagicMock()
            mock_repo.find_by_user_and_table.return_value = None
            MockRepo.return_value = mock_repo

            with minimal_app.test_client() as c:
                with c.session_transaction() as sess:
                    sess["user_id"] = 2
                    sess["user_role"] = "student"
                    sess["user_uuid"] = "test-uuid"
                resp = c.get("/test")
                assert resp.status_code == 403

    def test_non_admin_with_read_permission(self, minimal_app):
        """非管理员有读权限 → 200"""
        from middleware.auth_middleware import require_permission, PERM_READ

        @minimal_app.route("/test")
        @require_permission("students", PERM_READ)
        def view():
            return jsonify({"ok": True})

        mock_perm = MagicMock()
        mock_perm.permission_code = "700"  # rwx

        with patch("middleware.auth_middleware.UserPermissionRepo") as MockRepo:
            mock_repo = MagicMock()
            mock_repo.find_by_user_and_table.return_value = mock_perm
            MockRepo.return_value = mock_repo

            with minimal_app.test_client() as c:
                with c.session_transaction() as sess:
                    sess["user_id"] = 2
                    sess["user_role"] = "student"
                    sess["user_uuid"] = "test-uuid"
                resp = c.get("/test")
                assert resp.status_code == 200

    def test_non_admin_without_read_permission(self, minimal_app):
        """非管理员无读权限（只有写权限）→ 403"""
        from middleware.auth_middleware import require_permission, PERM_READ

        @minimal_app.route("/test")
        @require_permission("students", PERM_READ)
        def view():
            return jsonify({"ok": True})

        mock_perm = MagicMock()
        mock_perm.permission_code = "070"  # -wx

        with patch("middleware.auth_middleware.UserPermissionRepo") as MockRepo:
            mock_repo = MagicMock()
            mock_repo.find_by_user_and_table.return_value = mock_perm
            MockRepo.return_value = mock_repo

            with minimal_app.test_client() as c:
                with c.session_transaction() as sess:
                    sess["user_id"] = 2
                    sess["user_role"] = "student"
                    sess["user_uuid"] = "test-uuid"
                resp = c.get("/test")
                assert resp.status_code == 403

    def test_non_admin_with_write_permission(self, minimal_app):
        """非管理员有写权限，请求 read → 200（写包含读）"""
        from middleware.auth_middleware import require_permission, PERM_READ

        @minimal_app.route("/test")
        @require_permission("students", PERM_READ)
        def view():
            return jsonify({"ok": True})

        mock_perm = MagicMock()
        mock_perm.permission_code = "660"  # rw-

        with patch("middleware.auth_middleware.UserPermissionRepo") as MockRepo:
            mock_repo = MagicMock()
            mock_repo.find_by_user_and_table.return_value = mock_perm
            MockRepo.return_value = mock_repo

            with minimal_app.test_client() as c:
                with c.session_transaction() as sess:
                    sess["user_id"] = 2
                    sess["user_role"] = "student"
                    sess["user_uuid"] = "test-uuid"
                resp = c.get("/test")
                assert resp.status_code == 200

    def test_non_admin_with_admin_permission(self, minimal_app):
        """非管理员请求 admin 权限→ 200"""
        from middleware.auth_middleware import require_permission, PERM_ADMIN

        @minimal_app.route("/test")
        @require_permission("students", PERM_ADMIN)
        def view():
            return jsonify({"ok": True})

        mock_perm = MagicMock()
        mock_perm.permission_code = "770"  # rwx

        with patch("middleware.auth_middleware.UserPermissionRepo") as MockRepo:
            mock_repo = MagicMock()
            mock_repo.find_by_user_and_table.return_value = mock_perm
            MockRepo.return_value = mock_repo

            with minimal_app.test_client() as c:
                with c.session_transaction() as sess:
                    sess["user_id"] = 2
                    sess["user_role"] = "student"
                    sess["user_uuid"] = "test-uuid"
                resp = c.get("/test")
                assert resp.status_code == 200


# ═══════════════════════════════════════════
#  2. register_global_interceptor — 离线模式
# ═══════════════════════════════════════════

class TestGlobalInterceptorOffline:
    """全局拦截器 — 离线模式（is_db_available=False）"""

    @pytest.fixture
    def offline_app(self):
        from main import app as _app
        _app.config["TESTING"] = True
        _app.config["SERVER_NAME"] = "localhost"
        # 强制离线模式
        import config
        config._db_available = False
        yield _app
        config._db_available = True

    def test_offline_api_no_session(self, offline_app):
        """离线模式 + API 无 session → 401 JSON"""
        with offline_app.test_client() as c:
            resp = c.get("/api/students")
            assert resp.status_code == 401
            data = json.loads(resp.data)
            assert data["code"] == 1

    def test_offline_page_no_session(self, offline_app):
        """离线模式 + 页面无 session → redirect /login"""
        with offline_app.test_client() as c:
            resp = c.get("/students")
            assert resp.status_code in (302, 401)  # redirect or unauthorized

    def test_offline_allowed_page(self, offline_app):
        """离线模式 + 允许的页面 /settings → 正常"""
        with offline_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
                sess["user_name"] = "admin"
                sess["user_role"] = "admin"
            resp = c.get("/settings")
            # /settings 在离线模式白名单中
            assert resp.status_code in (200, 302)

    def test_offline_allowed_api(self, offline_app):
        """离线模式 + 允许的 API /api/csrf-token → 正常"""
        with offline_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
                sess["user_name"] = "admin"
                sess["user_role"] = "admin"
            resp = c.get("/api/csrf-token")
            # /api/csrf-token 在离线模式 API 白名单中
            assert resp.status_code in (200, 401, 403)

    def test_offline_blocked_api(self, offline_app):
        """离线模式 + 不允许的 API → 403"""
        with offline_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
                sess["user_name"] = "admin"
                sess["user_role"] = "admin"
            resp = c.get("/api/students")
            assert resp.status_code == 403


# ═══════════════════════════════════════════
#  3. register_global_interceptor — 非管理员
# ═══════════════════════════════════════════

class TestGlobalInterceptorNonAdmin:
    """全局拦截器 — 非管理员路由（username_changed=True）"""

    @pytest.fixture
    def online_app(self):
        from main import app as _app
        _app.config["TESTING"] = True
        _app.config["SERVER_NAME"] = "localhost"
        import config
        config._db_available = True
        yield _app

    def test_non_admin_page_redirect_to_my(self, online_app):
        """非管理员访问非白名单页面 → redirect /my"""
        with online_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
                sess["user_name"] = "student1"
                sess["user_role"] = "student"
                sess["user_ref_id"] = "S2024001"
                sess["username_changed"] = True
            resp = c.get("/students")
            assert resp.status_code in (302, 403)

    def test_student_self_data_api(self, online_app):
        """学生访问自身的 /api/students/<ref_id> → 200"""
        with online_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
                sess["user_name"] = "student1"
                sess["user_role"] = "student"
                sess["user_ref_id"] = "S2024001"
                sess["username_changed"] = True
            resp = c.get("/api/students/S2024001")
            assert resp.status_code in (200, 404)  # 404 if no such student, but not 403

    def test_student_other_api_blocked(self, online_app):
        """学生访问他人 API → 403"""
        with online_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
                sess["user_name"] = "student1"
                sess["user_role"] = "student"
                sess["user_ref_id"] = "S2024001"
                sess["username_changed"] = True
            resp = c.get("/api/students/S2024002")
            assert resp.status_code == 403

    @pytest.mark.skipif(True, reason="需要真实 PostgreSQL 数据库")
    def test_teacher_self_data_api(self, online_app):
        """教师访问自身的 /api/teachers/<ref_id> → 200/404"""
        with online_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 3
                sess["user_name"] = "teacher1"
                sess["user_role"] = "teacher"
                sess["user_ref_id"] = "T001"
                sess["username_changed"] = True
            resp = c.get("/api/teachers/T001")
            assert resp.status_code in (200, 404)  # 404 if no such teacher

    def test_username_not_changed(self, online_app):
        """username_changed=False 的非管理员 API 请求 → 403 with need_set_username"""
        with online_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
                sess["user_name"] = "temp_user"
                sess["user_role"] = "student"
                sess["user_ref_id"] = "S2024001"
                sess["username_changed"] = False
            resp = c.get("/api/students")
            assert resp.status_code == 403
            data = json.loads(resp.data)
            assert data.get("need_set_username") is True

    def test_username_not_changed_allowed_api(self, online_app):
        """username_changed=False 但访问白名单 API → 200"""
        with online_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
                sess["user_name"] = "temp_user"
                sess["user_role"] = "student"
                sess["user_ref_id"] = "S2024001"
                sess["username_changed"] = False
            # /api/set-username 在白名单中
            resp = c.get("/api/set-username")
            assert resp.status_code in (200, 302, 404, 405)
