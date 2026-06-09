# -*- coding: utf-8 -*-
"""Service 层单元测试 - 班级"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.class_service import ClassService
from service.department_service import DepartmentService
from service.major_service import MajorService


class TestClassService:
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
        s = ClassService()
        yield s
        s.close()

    def test_create(self, svc):
        obj = svc.create({"class_name": "计科1班", "major_id": 1, "enrollment_year": 2024})
        assert obj is not None
        assert obj.class_name == "计科1班"

    def test_get_all(self, svc):
        svc.create({"class_name": "class-a", "major_id": 1, "enrollment_year": 2024})
        svc.create({"class_name": "class-b", "major_id": 1, "enrollment_year": 2024})
        all_items = svc.get_all()
        assert len(all_items) == 2

    def test_get_list(self, svc):
        svc.create({"class_name": "class-a", "major_id": 1, "enrollment_year": 2024})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 1

    def test_update(self, svc):
        obj = svc.create({"class_name": "old-name", "major_id": 1, "enrollment_year": 2024})
        updated = svc.update(obj.class_id, {"class_name": "new-name"})
        assert updated is not None
        assert updated.class_name == "new-name"

    def test_update_not_found(self, svc):
        assert svc.update(9999, {"class_name": "x"}) is None

    def test_delete(self, svc):
        obj = svc.create({"class_name": "to-delete", "major_id": 1, "enrollment_year": 2024})
        assert svc.delete(obj.class_id) is True

    def test_delete_not_found(self, svc):
        assert svc.delete(9999) is False

    def test_close(self, svc):
        svc.close()
