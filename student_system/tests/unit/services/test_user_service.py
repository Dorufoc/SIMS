# -*- coding: utf-8 -*-
"""Service 层测试 — 用户管理"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine

from service.user_service import UserService
from entity.user import User
from entity.user_permission import UserPermission

class TestUserService:
    @pytest.fixture
    def svc(self):
        s = UserService()
        yield s
        s.close()

    def test_create(self, svc, reset_tables):
        ok, msg = svc.create({"username": "testuser", "password": "test123456", "role": "student"})
        assert ok is True

    def test_create_no_password(self, svc):
        ok, msg = svc.create({"username": "nopass"})
        assert ok is False
        assert "密码不能为空" in msg

    def test_create_duplicate(self, svc, reset_tables):
        ok, msg = svc.create({"username": "dupuser", "password": "test123", "role": "admin"})
        assert ok is True
        ok2, msg2 = svc.create({"username": "dupuser", "password": "test456", "role": "admin"})
        assert ok2 is False

    def test_update(self, svc, reset_tables):
        svc.create({"username": "upduser", "password": "test123", "role": "student"})
        # find the user
        from entity.base import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter(User.username == "upduser").first()
        db.close()
        ok, msg = svc.update(user.user_id, {"username": "updated_user", "role": "teacher"})
        assert ok is True

    def test_update_not_found(self, svc):
        ok, msg = svc.update(9999, {"username": "ghost"})
        assert ok is False

    def test_update_password(self, svc, reset_tables):
        svc.create({"username": "passuser", "password": "oldpass", "role": "student"})
        from entity.base import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter(User.username == "passuser").first()
        uid = user.user_id
        db.close()
        ok, msg = svc.update(uid, {"password": "New@67890"})
        assert ok is True

    def test_delete(self, svc, reset_tables):
        svc.create({"username": "deluser", "password": "test123", "role": "student"})
        from entity.base import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter(User.username == "deluser").first()
        uid = user.user_id
        db.close()
        assert svc.delete(uid) is True
        assert svc.delete(9999) is False

    def test_get_list(self, svc, reset_tables):
        svc.create({"username": "user1", "password": "p1", "role": "admin"})
        svc.create({"username": "user2", "password": "p2", "role": "teacher"})
        items, total = svc.get_list(page=1, page_size=10)
        assert total >= 2

    def test_get_list_with_keyword(self, svc, reset_tables):
        svc.create({"username": "searchable_user", "password": "p1", "role": "student"})
        items, total = svc.get_list(page=1, page_size=10, keyword="searchable")
        assert total >= 1

    def test_get_permissions(self, svc, reset_tables):
        svc.create({"username": "permuser", "password": "p1", "role": "student"})
        from entity.base import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter(User.username == "permuser").first()
        uid = user.user_id
        db.close()
        perms = svc.get_permissions(uid)
        assert len(perms) > 0

    def test_get_permissions_user_not_found(self, svc):
        perms = svc.get_permissions(9999)
        assert perms == []

    def test_set_permissions(self, svc, reset_tables):
        svc.create({"username": "setperm", "password": "p1", "role": "admin"})
        from entity.base import SessionLocal
        db = SessionLocal()
        user = db.query(User).filter(User.username == "setperm").first()
        uid = user.user_id
        db.close()
        ok, msg = svc.set_permissions(uid, [{"table_name": "students", "permission_code": "777"}])
        assert ok is True

    def test_set_permissions_user_not_found(self, svc):
        ok, msg = svc.set_permissions(9999, [{"table_name": "students", "permission_code": "777"}])
        assert ok is False

    def test_get_tables(self, svc):
        tables = svc.get_tables()
        assert len(tables) >= 10
        assert any(t["name"] == "students" for t in tables)
