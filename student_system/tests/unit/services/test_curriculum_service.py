# -*- coding: utf-8 -*-
"""Service 层单元测试 - 培养计划"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.curriculum_service import CurriculumService
from service.department_service import DepartmentService
from service.major_service import MajorService
from service.course_service import CourseService


class TestCurriculumService:
    @pytest.fixture
    def setup_db(self):
        import entity
        from sqlalchemy import text
        # TRUNCATE all tables (much faster than drop_all + create_all)
        tables_list = ', '.join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        if tables_list:
            with engine.connect() as conn:
                conn.execute(text(f'TRUNCATE TABLE {tables_list} RESTART IDENTITY CASCADE'))
                conn.commit()
        yield

    @pytest.fixture
    def svc(self, setup_db):
        ds = DepartmentService()
        ds.create({"dept_name": "test-dept"})
        ds.close()
        ms = MajorService()
        ms.create({"major_name": "test-major", "dept_id": 1, "duration": 4})
        ms.close()
        cs = CourseService()
        cs.create({"course_id": "CS101", "course_name": "数据结构", "credits": 4, "hours": 64, "type": "必修"})
        cs.close()
        s = CurriculumService()
        yield s
        s.close()

    def test_create(self, svc):
        obj = svc.create({"course_id": "CS101", "major_id": 1, "enrollment_year": 2024, "recommended_term": "1"})
        assert obj is not None
        assert obj.course_id == "CS101"

    def test_get_list(self, svc):
        svc.create({"course_id": "CS101", "major_id": 1, "enrollment_year": 2024})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 1

    def test_update(self, svc):
        svc.create({"course_id": "CS101", "major_id": 1, "enrollment_year": 2024})
        updated = svc.update(1, {"recommended_term": "2"})
        assert updated is not None
        assert updated.recommended_term == "2"

    def test_update_not_found(self, svc):
        assert svc.update(9999, {"recommended_term": "2"}) is None

    def test_delete(self, svc):
        svc.create({"course_id": "CS101", "major_id": 1, "enrollment_year": 2024})
        assert svc.delete(1) is True

    def test_delete_not_found(self, svc):
        assert svc.delete(9999) is False

    def test_close(self, svc):
        svc.close()
