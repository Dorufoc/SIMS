# -*- coding: utf-8 -*-
"""Repository 层单元测试"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from repository.user_repo import UserRepo
from entity.user import User
from utils.permission_utils import generate_uuid

class TestUserRepo:
    @pytest.fixture
    def repo(self, reset_tables):
        Base.metadata.create_all(bind=engine)
        r = UserRepo()
        yield r
        r.close()

    def _create_test_user(self, repo):
        u = User(uuid=generate_uuid(), username="repouser1", role="student", password_hash="hash")
        repo.create(u)
        return u

    def test_find_by_username(self, repo):
        u = self._create_test_user(repo)
        found = repo.find_by_username("repouser1")
        assert found is not None

    def test_find_by_uuid(self, repo):
        u = self._create_test_user(repo)
        found = repo.find_by_uuid(u.uuid)
        assert found is not None

    def test_find_by_identifier(self, repo):
        # 管理员可通过用户名作为 identifier 查找
        u = User(uuid=generate_uuid(), username="adminuser1", role="admin", password_hash="hash")
        repo.create(u)
        found = repo.find_by_identifier("adminuser1")
        assert found is not None
        assert found.username == "adminuser1"

    def test_find_by_identifier_ref_id(self, repo):
        u = User(uuid=generate_uuid(), username="stuuser1", role="student",
                 password_hash="hash", ref_id="SREF001")
        repo.create(u)
        found = repo.find_by_identifier("SREF001")
        assert found is not None
        assert found.ref_id == "SREF001"

    def test_find_by_ref_id(self, repo):
        u = User(uuid=generate_uuid(), username="repouser2", role="student", password_hash="hash", ref_id="REF001")
        repo.create(u)
        found = repo.find_by_ref_id("REF001")
        assert found is not None

    def test_find_by_email(self, repo):
        u = User(uuid=generate_uuid(), username="emailuser", role="student", password_hash="hash", email="test@example.com")
        repo.create(u)
        found = repo.find_by_email("test@example.com")
        assert found is not None
        assert found.username == "emailuser"

    def test_find_by_email_not_found(self, repo):
        found = repo.find_by_email("missing@example.com")
        assert found is None

    def test_find_by_phone(self, repo):
        u = User(uuid=generate_uuid(), username="phoneuser", role="student", password_hash="hash", phone="13800138000")
        repo.create(u)
        found = repo.find_by_phone("13800138000")
        assert found is not None
        assert found.username == "phoneuser"

    def test_find_by_phone_not_found(self, repo):
        found = repo.find_by_phone("00000000000")
        assert found is None
