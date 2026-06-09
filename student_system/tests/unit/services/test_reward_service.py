# -*- coding: utf-8 -*-
"""Service 层复杂测试 — 奖惩"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine
from service.reward_service import RewardService
from service.student_service import StudentService


class TestRewardService:
    @pytest.fixture
    def setup(self):
        import entity  # noqa: F401
        from sqlalchemy import text
        # TRUNCATE all tables (much faster than drop_all + create_all)
        tables_list = ', '.join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        if tables_list:
            with engine.connect() as conn:
                conn.execute(text(f'TRUNCATE TABLE {tables_list} RESTART IDENTITY CASCADE'))
                conn.commit()
        stu_svc = StudentService()
        stu_svc.create({"student_id": "S001", "name": "测试学生", "enrollment_year": 2024})
        stu_svc.close()
        yield

    @pytest.fixture
    def svc(self, setup):
        s = RewardService()
        yield s
        s.close()

    def test_create(self, svc):
        rp = svc.create({"student_id": "S001", "rp_type": "奖励", "title": "优秀学生",
                         "level": "校级", "date": "2024-12-01", "reason": "成绩优异"})
        assert rp is not None
        assert rp.title == "优秀学生"

    def test_get_by_student(self, svc):
        svc.create({"student_id": "S001", "rp_type": "奖励", "title": "优秀学生",
                    "level": "校级", "date": "2024-12-01"})
        results = svc.get_by_student("S001")
        assert len(results) == 1

    def test_update(self, svc):
        svc.create({"student_id": "S001", "rp_type": "奖励", "title": "旧标题",
                    "date": "2024-12-01"})
        updated = svc.update(1, {"title": "新标题"})
        assert updated is not None
        assert updated.title == "新标题"

    def test_update_not_found(self, svc):
        assert svc.update(999, {"title": "x"}) is None

    def test_delete(self, svc):
        svc.create({"student_id": "S001", "rp_type": "奖励", "title": "待删除",
                    "date": "2024-12-01"})
        assert svc.delete(1) is True

    def test_delete_nonexistent(self, svc):
        assert svc.delete(999) is False
