# -*- coding: utf-8 -*-
"""Repository 层单元测试 - UserPermissionRepo"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from repository.user_permission_repo import UserPermissionRepo
from entity.user import User
from utils.permission_utils import generate_uuid


@pytest.fixture
def repo(reset_tables):
    import entity  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # 先创建测试用户（UserPermission 有 FK -> users.uuid）
    from entity.base import SessionLocal
    db = SessionLocal()
    for uid, uuid_str in [(1, "uuid-001"), (2, "uuid-002"), (3, "uuid-003"), (4, "uuid-004")]:
        u = User(user_id=uid, uuid=uuid_str, username=f"user{uid}",
                 password_hash="hash", role="admin")
        db.add(u)
    db.commit()
    db.close()
    r = UserPermissionRepo()
    yield r
    r.close()


class TestUserPermissionRepo:
    def test_upsert_insert(self, repo):
        p = repo.upsert("uuid-001", "students", "777")
        assert p is not None
        assert p.permission_code == "777"

    def test_upsert_update(self, repo):
        repo.upsert("uuid-002", "courses", "400")
        p2 = repo.upsert("uuid-002", "courses", "600")
        assert p2.permission_code == "600"

    def test_find_by_user_uuid(self, repo):
        repo.upsert("uuid-003", "students", "777")
        repo.upsert("uuid-003", "courses", "400")
        perms = repo.find_by_user_uuid("uuid-003")
        assert len(perms) == 2

    def test_find_by_user_and_table(self, repo):
        repo.upsert("uuid-004", "majors", "600")
        p = repo.find_by_user_and_table("uuid-004", "majors")
        assert p is not None
        assert p.permission_code == "600"

    def test_delete_by_user_uuid(self, repo):
        repo.upsert("uuid-001", "students", "777")
        repo.upsert("uuid-001", "courses", "400")
        repo.delete_by_user_uuid("uuid-001")
        perms = repo.find_by_user_uuid("uuid-001")
        assert len(perms) == 0

    def test_delete_by_user_uuid_no_records(self, repo):
        # 删除不存在的用户权限记录不应抛出异常
        repo.delete_by_user_uuid("uuid-no-perms")
        perms = repo.find_by_user_uuid("uuid-no-perms")
        assert len(perms) == 0
