# -*- coding: utf-8 -*-
"""Service 层复杂测试 — 认证"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.auth_service import AuthService


class TestAuthService:
    @pytest.fixture
    def svc(self):
        s = AuthService()
        yield s
        s.close()

    @pytest.fixture
    def reset_tables(self):
        import entity  # noqa: F401
        from sqlalchemy import text
        # TRUNCATE all tables (much faster than drop_all + create_all)
        tables_list = ', '.join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        if tables_list:
            with engine.connect() as conn:
                conn.execute(text(f'TRUNCATE TABLE {tables_list} RESTART IDENTITY CASCADE'))
                conn.commit()
        yield

    def test_login_nonexistent(self, svc, reset_tables):
        ok, msg, user = svc.login("nonexistent", "pass")
        assert ok is False
        assert "错误" in msg
        assert user is None

    def test_register_and_login(self, svc, reset_tables):
        ok, msg, user = svc.register("testpass123", "测试学生", "student", "ref_id", "S999999")
        assert ok is True
        assert user is not None
        assert user["username"].startswith("tmp_")
        ok2, msg2, user2 = svc.login(user["username"], "testpass123")
        assert ok2 is True

    def test_register_short_password(self, svc):
        ok, msg, user = svc.register("12", "short", "student", "ref_id", "S000001")
        assert ok is False

    def test_set_username(self, svc, reset_tables):
        ok, msg, _ = svc.register("test123456", "测试", "student", "ref_id", "S100001")
        assert ok is True
        from entity.user import User
        from entity.base import SessionLocal
        db = SessionLocal()
        u = db.query(User).filter(User.ref_id == "S100001").first()
        ok2, msg2, name = svc.set_username(u.user_id, "newuser1")
        assert ok2 is True
        assert name == "newuser1"
        db.close()

    def test_set_username_too_short(self, svc):
        ok, msg, _ = svc.set_username(1, "ab")
        assert ok is False

    def test_change_password(self, svc, reset_tables):
        ok, msg, _ = svc.register("oldpass123", "测试", "student", "ref_id", "S200001")
        assert ok is True
        from entity.user import User
        from entity.base import SessionLocal
        db = SessionLocal()
        u = db.query(User).filter(User.ref_id == "S200001").first()
        ok2, msg2 = svc.change_password(u.user_id, "oldpass123", "newpass456")
        assert ok2 is True
        db.close()
