# -*- coding: utf-8 -*-
"""Service 层单元测试 - 课程"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.course_service import CourseService


class TestCourseService:
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
        s = CourseService()
        yield s
        s.close()

    def test_create(self, svc):
        obj = svc.create({"course_id": "CS101", "course_name": "数据结构", "credits": 4.0, "hours": 64, "type": "必修"})
        assert obj is not None
        assert obj.course_name == "数据结构"

    def test_get_all(self, svc):
        svc.create({"course_id": "CS101", "course_name": "course-a", "credits": 3, "type": "必修"})
        svc.create({"course_id": "CS102", "course_name": "course-b", "credits": 4, "type": "选修"})
        all_items = svc.get_all()
        assert len(all_items) == 2

    def test_get_list(self, svc):
        svc.create({"course_id": "CS101", "course_name": "course-a", "credits": 3, "type": "必修"})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 1

    def test_update(self, svc):
        svc.create({"course_id": "CS101", "course_name": "old-name", "credits": 3, "type": "必修"})
        updated = svc.update("CS101", {"course_name": "new-name"})
        assert updated is not None
        assert updated.course_name == "new-name"

    def test_update_not_found(self, svc):
        assert svc.update("NONEXIST", {"course_name": "x"}) is None

    def test_delete(self, svc):
        svc.create({"course_id": "CS101", "course_name": "to-delete", "credits": 3, "type": "必修"})
        assert svc.delete("CS101") is True

    def test_delete_not_found(self, svc):
        assert svc.delete("NONEXIST") is False

    def test_close(self, svc):
        svc.close()
