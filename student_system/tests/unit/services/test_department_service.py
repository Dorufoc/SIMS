# -*- coding: utf-8 -*-
"""Service 层单元测试 - 院系"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.department_service import DepartmentService


class TestDepartmentService:
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
    def svc(self):
        s = DepartmentService()
        yield s
        s.close()

    def test_create(self, setup_db, svc):
        obj = svc.create({"dept_name": "test-dept", "dean": "张教授", "phone": "010-12345678"})
        assert obj is not None
        assert obj.dept_name == "test-dept"

    def test_get_all(self, setup_db, svc):
        svc.create({"dept_name": "dept-a"})
        svc.create({"dept_name": "dept-b"})
        all_depts = svc.get_all()
        assert len(all_depts) == 2

    def test_get_list(self, setup_db, svc):
        svc.create({"dept_name": "dept-a"})
        svc.create({"dept_name": "dept-b"})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 2
        assert len(items) == 2

    def test_update(self, setup_db, svc):
        obj = svc.create({"dept_name": "old-name"})
        updated = svc.update(obj.dept_id, {"dept_name": "new-name"})
        assert updated is not None
        assert updated.dept_name == "new-name"

    def test_update_not_found(self, setup_db, svc):
        result = svc.update(9999, {"dept_name": "x"})
        assert result is None

    def test_delete(self, setup_db, svc):
        obj = svc.create({"dept_name": "to-delete"})
        assert svc.delete(obj.dept_id) is True

    def test_delete_not_found(self, setup_db, svc):
        assert svc.delete(9999) is False

    def test_close(self, svc):
        svc.close()
