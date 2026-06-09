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
    def repo(self):
        Base.metadata.create_all(bind=engine)
        r = UserRepo()
        yield r
        r.close()
        Base.metadata.drop_all(bind=engine)

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
        u = self._create_test_user(repo)
        found = repo.find_by_identifier("repouser1")
        assert found is not None

    def test_find_by_ref_id(self, repo):
        u = User(uuid=generate_uuid(), username="repouser2", role="student", password_hash="hash", ref_id="REF001")
        repo.create(u)
        found = repo.find_by_ref_id("REF001")
        assert found is not None
