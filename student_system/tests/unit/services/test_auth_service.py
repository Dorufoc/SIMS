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

    def _create_student(self, student_id):
        """为学生注册测试创建必要的 Student 记录"""
        from entity.base import SessionLocal
        from entity.student import Student
        db = SessionLocal()
        s = Student(student_id=student_id, name="测试", enrollment_year=2024)
        db.add(s)
        db.commit()
        db.close()

    def test_register_and_login(self, svc, reset_tables):
        self._create_student("S999999")
        ok, msg, user = svc.register("Test@12345", "测试学生", "student", "ref_id", "S999999")
        assert ok is True
        assert user is not None
        assert user["username"].startswith("tmp_")
        # login by ref_id (非管理员用户通过 ref_id 匹配)
        ok2, msg2, user2 = svc.login("S999999", "Test@12345")
        assert ok2 is True

    def test_register_short_password(self, svc):
        ok, msg, user = svc.register("12", "short", "student", "ref_id", "S000001")
        assert ok is False

    def test_set_username(self, svc, reset_tables):
        self._create_student("S100001")
        ok, msg, _ = svc.register("Test@12345", "测试", "student", "ref_id", "S100001")
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
        self._create_student("S200001")
        ok, msg, _ = svc.register("Old@12345", "测试", "student", "ref_id", "S200001")
        assert ok is True
        from entity.user import User
        from entity.base import SessionLocal
        db = SessionLocal()
        u = db.query(User).filter(User.ref_id == "S200001").first()
        ok2, msg2 = svc.change_password(u.user_id, "Old@12345", "New@67890")
        assert ok2 is True
        db.close()

    def test_local_login_success(self):
        ok, msg, user = AuthService.local_login("admin", "admin")
        assert ok is True
        assert "离线模式" in msg
        assert user["role"] == "admin"
        assert user["user_id"] == 0

    def test_local_login_wrong_password(self):
        ok, msg, user = AuthService.local_login("admin", "wrong")
        assert ok is False
        assert "错误" in msg
        assert user is None

    def test_local_login_unknown_user(self):
        ok, msg, user = AuthService.local_login("nobody", "admin")
        assert ok is False
        assert user is None
