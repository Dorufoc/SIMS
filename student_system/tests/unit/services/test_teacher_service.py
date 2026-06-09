# -*- coding: utf-8 -*-
"""Service 层单元测试 - 教师"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.teacher_service import TeacherService


class TestTeacherService:
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
        s = TeacherService()
        yield s
        s.close()

    def test_create(self, svc):
        obj = svc.create({"teacher_id": "T001", "name": "李教授", "gender": "M", "title": "教授"})
        assert obj is not None
        assert obj.name == "李教授"

    def test_get_all(self, svc):
        svc.create({"teacher_id": "T001", "name": "teacher-a"})
        svc.create({"teacher_id": "T002", "name": "teacher-b"})
        all_items = svc.get_all()
        assert len(all_items) == 2

    def test_get_list(self, svc):
        svc.create({"teacher_id": "T001", "name": "teacher-a", "title": "教授"})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 1

    def test_update(self, svc):
        svc.create({"teacher_id": "T001", "name": "old-name"})
        updated = svc.update("T001", {"name": "new-name"})
        assert updated is not None
        assert updated.name == "new-name"

    def test_update_not_found(self, svc):
        assert svc.update("NONEXIST", {"name": "x"}) is None

    def test_delete(self, svc):
        svc.create({"teacher_id": "T001", "name": "to-delete"})
        assert svc.delete("T001") is True

    def test_delete_not_found(self, svc):
        assert svc.delete("NONEXIST") is False

    def test_close(self, svc):
        svc.close()
