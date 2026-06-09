# -*- coding: utf-8 -*-
"""Service 层单元测试 - 授课"""
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine

from service.teaching_service import TeachingService
from service.course_service import CourseService
from service.teacher_service import TeacherService
from service.semester_service import SemesterService


class TestTeachingService:
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
        cs = CourseService()
        cs.create({"course_id": "CS101", "course_name": "数据结构", "credits": 4, "hours": 64, "type": "必修"})
        cs.close()
        ts = TeacherService()
        ts.create({"teacher_id": "T001", "name": "李教授"})
        ts.close()
        ss = SemesterService()
        ss.create({"academic_year": "2024-2025", "semester_name": "first", "start_date": "2024-09-01", "end_date": "2025-01-15"})
        ss.close()
        s = TeachingService()
        yield s
        s.close()

    def test_create(self, svc):
        obj = svc.create({"course_id": "CS101", "teacher_id": "T001", "semester_id": 1, "classroom": "A101", "schedule": "周一 1-2节", "capacity": 60})
        assert obj is not None
        assert obj.course_id == "CS101"

    def test_get_list(self, svc):
        svc.create({"course_id": "CS101", "teacher_id": "T001", "semester_id": 1})
        items, total = svc.get_list(page=1, page_size=10)
        assert total == 1

    def test_update(self, svc):
        svc.create({"course_id": "CS101", "teacher_id": "T001", "semester_id": 1})
        updated = svc.update(1, {"classroom": "B202"})
        assert updated is not None
        assert updated.classroom == "B202"

    def test_update_not_found(self, svc):
        assert svc.update(9999, {"classroom": "x"}) is None

    def test_delete(self, svc):
        svc.create({"course_id": "CS101", "teacher_id": "T001", "semester_id": 1})
        assert svc.delete(1) is True

    def test_delete_not_found(self, svc):
        assert svc.delete(9999) is False

    def test_close(self, svc):
        svc.close()
