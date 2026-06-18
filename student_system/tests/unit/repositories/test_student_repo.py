# -*- coding: utf-8 -*-
"""Repository 层单元测试"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from repository.student_repo import StudentRepo
from entity.student import Student

class TestStudentRepo:
    @pytest.fixture
    def repo(self, reset_tables):
        Base.metadata.create_all(bind=engine)
        r = StudentRepo()
        yield r
        r.close()

    def test_find_by_student_id(self, repo):
        s = Student(student_id="R001", name="repotest", enrollment_year=2024)
        repo.create(s)
        found = repo.find_by_student_id("R001")
        assert found is not None
        assert found.name == "repotest"

    def test_search(self, repo):
        s = Student(student_id="R002", name="search_target", enrollment_year=2024)
        repo.create(s)
        items, total = repo.search("search_target", page=1, page_size=10)
        assert total >= 1
