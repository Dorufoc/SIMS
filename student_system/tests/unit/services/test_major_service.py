# -*- coding: utf-8 -*-
"""Service 层单元测试 - 专业"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.major_service import MajorService
from service.department_service import DepartmentService


class TestMajorService:
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
        s = MajorService()
        ds = DepartmentService()
        ds.create({"dept_name": "test-dept"})
        ds.close()
        yield s
        s.close()

    def test_create(self, svc):
        obj = svc.create({"major_name": "计算机科学与技术", "dept_id": 1, "duration": 4})
        assert obj is not None
        assert obj.major_name == "计算机科学与技术"

    def test_get_all(self, svc):
        svc.create({"major_name": "major-a", "dept_id": 1, "duration": 4})
        svc.create({"major_name": "major-b", "dept_id": 1, "duration": 3})
        all_items = svc.get_all()
        assert len(all_items) == 2

    def test_get_list(self, svc):
        svc.create({"major_name": "major-a", "dept_id": 1, "duration": 4})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 1
        assert len(items) == 1

    def test_update(self, svc):
        obj = svc.create({"major_name": "old-name", "dept_id": 1, "duration": 4})
        updated = svc.update(obj.major_id, {"major_name": "new-name"})
        assert updated is not None
        assert updated.major_name == "new-name"

    def test_update_not_found(self, svc):
        assert svc.update(9999, {"major_name": "x"}) is None

    def test_delete(self, svc):
        obj = svc.create({"major_name": "to-delete", "dept_id": 1, "duration": 4})
        assert svc.delete(obj.major_id) is True

    def test_delete_not_found(self, svc):
        assert svc.delete(9999) is False

    def test_close(self, svc):
        svc.close()
