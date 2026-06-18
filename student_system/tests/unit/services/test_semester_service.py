# -*- coding: utf-8 -*-
"""Service 层单元测试 - 学期"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.semester_service import SemesterService


class TestSemesterService:
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
        s = SemesterService()
        yield s
        s.close()

    def test_create(self, svc):
        obj = svc.create({"academic_year": "2025-2026", "semester_name": "第一学期", "start_date": "2025-09-01", "end_date": "2026-01-15"})
        assert obj is not None
        assert obj.academic_year == "2025-2026"

    def test_get_all(self, svc):
        svc.create({"academic_year": "2024-2025", "semester_name": "first", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        svc.create({"academic_year": "2025-2026", "semester_name": "second", "start_date": "2025-09-01", "end_date": "2026-01-15"})
        all_items = svc.get_all()
        assert len(all_items) == 2

    def test_get_list(self, svc):
        svc.create({"academic_year": "2024-2025", "semester_name": "first", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 1

    def test_update(self, svc):
        svc.create({"academic_year": "2024-2025", "semester_name": "old", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        updated = svc.update(1, {"semester_name": "new"})
        assert updated is not None
        assert updated.semester_name == "new"

    def test_update_not_found(self, svc):
        assert svc.update(9999, {"semester_name": "x"}) is None

    def test_delete(self, svc):
        svc.create({"academic_year": "2024-2025", "semester_name": "to-delete", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        assert svc.delete(1) is True

    def test_delete_not_found(self, svc):
        assert svc.delete(9999) is False

    def test_close(self, svc):
        svc.close()

    def test_get_by_id(self, svc):
        created = svc.create({"academic_year": "2024-2025", "semester_name": "第一学期", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        found = svc.get_by_id(created.semester_id)
        assert found is not None
        assert found.semester_id == created.semester_id

    def test_get_by_id_not_found(self, svc):
        assert svc.get_by_id(9999) is None

    def test_set_current(self, svc):
        s1 = svc.create({"academic_year": "2024-2025", "semester_name": "第一学期", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        s2 = svc.create({"academic_year": "2025-2026", "semester_name": "第二学期", "start_date": "2025-09-01", "end_date": "2026-01-15"})
        assert svc.set_current(s2.semester_id) is True
        assert svc.get_by_id(s1.semester_id).is_current is False
        assert svc.get_by_id(s2.semester_id).is_current is True

    def test_set_current_not_found(self, svc):
        # 先创建一条记录，避免 get_all 为空时产生意外
        svc.create({"academic_year": "2024-2025", "semester_name": "第一学期", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        assert svc.set_current(9999) is False

    def test_get_current(self, svc):
        s = svc.create({"academic_year": "2024-2025", "semester_name": "第一学期", "start_date": "2024-09-01", "end_date": "2025-01-15", "is_current": True})
        current = svc.get_current()
        assert current is not None
        assert current.semester_id == s.semester_id

    def test_get_current_none(self, svc):
        assert svc.get_current() is None
