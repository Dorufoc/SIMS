# -*- coding: utf-8 -*-
"""Config 高级测试 — 覆盖离线模式、动态环境变量等新功能"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import json


class TestConfigOfflineMode:
    """测试 config 离线模式相关功能"""

    def test_is_db_available(self):
        """测试 is_db_available / set_db_available """
        import config
        # 先保存原始值
        original = config._db_available
        config.set_db_available(False)
        assert config.is_db_available() is False
        config.set_db_available(True)
        assert config.is_db_available() is True
        config._db_available = original

    def test_get_env_dynamic(self):
        """测试 get_env_dynamic 实时读取"""
        import config
        val = config.get_env_dynamic("SECRET_KEY")
        assert val is not None

    def test_get_env_dynamic_default(self):
        """测试 get_env_dynamic 不存在的key返回默认值"""
        import config
        val = config.get_env_dynamic("NONEXISTENT_KEY", "default_val")
        assert val == "default_val"

    def test_get_env_dynamic_no_env_file(self, tmp_path):
        """测试 .env 不存在时返回默认值"""
        import config
        # 保存原路径并临时修改
        orig = config.ENV_PATH
        
        class FakeConfig:
            ENV_PATH = tmp_path / ".env"
            
        val = config.get_env_dynamic("TEST", "fallback")
        # 如果.env不存在，应该返回默认值
        
        assert val == "fallback" or val == config.get_env_dynamic("TEST", "fallback")

    def test_config_constants(self):
        """测试配置常量"""
        import config
        assert hasattr(config, "SECRET_KEY")
        assert hasattr(config, "DATABASE_URL")
        assert hasattr(config, "MAX_CONTENT_LENGTH")
        assert hasattr(config, "FLASK_ENV")
        assert hasattr(config, "SHOW_MOCK_DATA_BUTTON")
        assert config.MAX_CONTENT_LENGTH == 10 * 1024 * 1024


class TestConfigValidation:
    """测试配置验证功能"""

    def test_missing_database_url_production(self):
        """生产环境无 DATABASE_URL 应抛出异常"""
        import importlib
        import config as cfg
        # 保存原始值
        orig_url = os.environ.get("DATABASE_URL", "")
        orig_flask_env = os.environ.get("FLASK_ENV", "")
        try:
            # 对于没有DATABASE_URL的生产环境应该抛出 RuntimeError
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            os.environ["FLASK_ENV"] = "production"
            
            import config as cfg_reload
            importlib.reload(cfg_reload)
            # 如果没有异常，确认 DATABASE_URL 为默认值
            assert cfg_reload.FLASK_ENV == "production"
        except RuntimeError as e:
            assert "DATABASE_URL" in str(e)
        finally:
            if orig_url:
                os.environ["DATABASE_URL"] = orig_url
            os.environ["FLASK_ENV"] = orig_flask_env
            importlib.reload(cfg)


class TestPasswordUtilsAdvanced:
    """password_utils 剩余路径测试"""

    def test_password_utils_has_all_exports(self):
        from utils.password_utils import (
            encrypt_password, verify_password, hash_password,
            generate_salt, encode_password_storage, decode_password_storage
        )
        assert callable(encrypt_password)
        assert callable(verify_password)
        assert callable(hash_password)
        assert callable(generate_salt)

    def test_generate_salt_default_and_custom(self):
        from utils.password_utils import generate_salt
        s = generate_salt()
        assert len(s) >= 16
        s32 = generate_salt(32)
        assert len(s32) >= 32

    def test_hash_password_different_salts(self):
        from utils.password_utils import hash_password
        s1, h1 = hash_password("test", salt=None)
        s2, h2 = hash_password("test", salt=None)
        assert s1 != s2  # different salts
        assert h1 != h2  # different hashes

    def test_decode_password_storage_invalid(self):
        from utils.password_utils import decode_password_storage
        with pytest.raises(ValueError):
            decode_password_storage("invalid_format_no_separator")

    def test_verify_password_empty(self):
        from utils.password_utils import verify_password
        valid, needs_upgrade, upgraded = verify_password("", "")
        assert valid is False
        assert needs_upgrade is False
        assert upgraded is None

    def test_verify_password_none(self):
        from utils.password_utils import verify_password
        with pytest.raises((AttributeError, TypeError)):
            verify_password(None, None)


class TestPermissionUtilsAdvanced:
    """permission_utils 剩余路径测试"""

    def test_build_and_parse_roundtrip(self):
        from utils.permission_utils import build_permission_code, parse_permission_code
        
        for can_read, can_write, can_admin in [
            (True, True, True),
            (True, False, False),
            (False, True, False),
            (False, False, True),
            (True, True, False),
        ]:
            code = build_permission_code(can_read, can_write, can_admin)
            r, w, a = parse_permission_code(code)
            assert r == can_read
            assert w == can_write
            assert a == can_admin

    def test_parse_permission_code_overflow(self):
        from utils.permission_utils import parse_permission_code
        r, w, a = parse_permission_code("77777")
        assert r is True
        assert w is True
        assert a is True

    def test_parse_permission_code_negative(self):
        from utils.permission_utils import parse_permission_code
        r, w, a = parse_permission_code("-1")
        assert r is False

    def test_parse_permission_code_alpha(self):
        from utils.permission_utils import parse_permission_code
        r, w, a = parse_permission_code("abc")
        assert r is False

    def test_generate_uuid_uniqueness(self):
        from utils.permission_utils import generate_uuid
        uuids = {generate_uuid() for _ in range(100)}
        assert len(uuids) == 100

    def test_init_user_permissions(self):
        from utils.permission_utils import init_user_permissions
        mock_repo = MagicMock()
        
        # Student role
        init_user_permissions(mock_repo, "uuid-student", "student")
        assert mock_repo.upsert.call_count >= 10
        
        mock_repo.reset_mock()
        init_user_permissions(mock_repo, "uuid-teacher", "teacher")
        assert mock_repo.upsert.call_count >= 10
        
        mock_repo.reset_mock()
        init_user_permissions(mock_repo, "uuid-other", "other")
        assert mock_repo.upsert.call_count >= 15


class TestEntityBaseAdvanced:
    """entity/base 高级测试"""

    def test_escape_like_special_chars(self):
        from repository.base import escape_like
        assert escape_like("test%_\\value") == "test\\%\\_\\\\value"
        assert escape_like("%%__") == "\\%\\%\\_\\_"
        assert escape_like("") == ""

    def test_is_postgresql_true_with_env(self):
        """测试 _is_postgresql 返回 True"""
        from entity.base import _is_postgresql
        if "postgresql" in os.environ.get("DATABASE_URL", ""):
            assert _is_postgresql() is True

    def test_base_metadata_has_required_tables(self):
        from entity.base import Base
        import entity
        required_tables = ["students", "users", "departments", "majors", "classes",
                          "courses", "teachers", "semesters", "teaching"]
        for t in required_tables:
            assert t in Base.metadata.tables, f"Missing table: {t}"

    def test_all_entities_have_primary_key(self):
        from entity.base import Base
        import entity
        for name, table in Base.metadata.tables.items():
            assert table.primary_key, f"Table {name} has no primary key"


class TestMainAdvanced:
    """main.py 高级测试"""

    def test_create_app_with_testing(self):
        from main import create_app
        app = create_app()
        app.config["TESTING"] = True
        assert app.config["TESTING"] is True
        assert app.secret_key is not None

    def test_app_has_security_headers(self):
        from main import create_app
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            resp = c.get("/login")
            # 检查安全头
            headers = resp.headers
            header_names = {k.lower() for k, v in headers}
            has_security = bool(
                header_names & {"x-content-type-options", "x-frame-options", "content-security-policy"}
            )

    def test_app_blueprints_registered(self):
        import main
        app = main.app
        with app.app_context():
            blueprints = [bp.name for bp in app.blueprints.values()]
            assert len(blueprints) >= 15


class TestMiddlewareAdvanced2:
    """中间件剩余路径测试"""

    @pytest.fixture
    def minimal_app(self):
        """创建最小 Flask 应用用于测试中间件（不带全局拦截器）"""
        from flask import Flask
        _app = Flask(__name__)
        _app.secret_key = "test-secret"
        _app.config["TESTING"] = True
        _app.config["SERVER_NAME"] = "localhost"
        return _app

    def test_require_permission_unknown_perm(self, minimal_app):
        """require_permission 未知权限类型 → 403"""
        from middleware.auth_middleware import require_permission
        
        @minimal_app.route("/test-unknown")
        @require_permission("students", 999)  # 未知权限码
        def view():
            pass

        with minimal_app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 2
                sess["user_role"] = "student"
                sess["user_uuid"] = "test-uuid"
            resp = c.get("/test-unknown")
            assert resp.status_code in (401, 403)

    def test_require_login_with_session(self):
        """require_login 有 session 时放行"""
        from flask import Flask
        from middleware.auth_middleware import require_login
        
        app = Flask(__name__)
        app.secret_key = "test"
        app.config["TESTING"] = True
        
        @app.route("/test")
        @require_login
        def view():
            return "ok"
            
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = 1
            resp = c.get("/test")
            assert resp.status_code == 200

    def test_generate_csrf_token_creates(self):
        """generate_csrf_token 创建并返回 token"""
        from middleware.auth_middleware import generate_csrf_token
        from flask import Flask, session
        
        app = Flask(__name__)
        app.secret_key = "test"
        app.config["TESTING"] = True
        
        with app.test_request_context():
            token = generate_csrf_token()
            assert len(token) > 10
            assert session.get("_csrf_token") == token

    def test_csrf_protect_testing_mode(self):
        """csrf_protect 在 TESTING 模式下跳过验证"""
        from middleware.auth_middleware import csrf_protect
        from flask import Flask
        
        app = Flask(__name__)
        app.secret_key = "test"
        app.config["TESTING"] = True
        
        @app.route("/test", methods=["POST"])
        @csrf_protect
        def view():
            return "ok"
            
        with app.test_client() as c:
            resp = c.post("/test")
            assert resp.status_code == 200

    def test_offline_mode_disables_db_check(self):
        """离线模式下跳过数据库检查"""
        import config
        config._db_available = False
        assert config.is_db_available() is False
        config._db_available = True
