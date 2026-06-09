# -*- coding: utf-8 -*-
"""Service 层测试 — 宿舍服务"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine

from service.dorm_service import DormService
from entity.dorm_room import DormRoom
from entity.dorm_assignment import DormAssignment
from entity.student import Student
from entity.department import Department
from entity.major import Major
from entity.class_ import Class

class TestDormService:
    @pytest.fixture
    def svc(self):
        s = DormService()
        yield s
        s.close()

    def _setup_student(self):
        from entity.base import SessionLocal
        db = SessionLocal()
        dept = Department(dept_name="测试学院")
        db.add(dept); db.flush()
        major = Major(major_name="测试专业", dept_id=dept.dept_id, duration=4)
        db.add(major); db.flush()
        cls = Class(class_name="测试班", major_id=major.major_id, enrollment_year=2024)
        db.add(cls); db.flush()
        stu = Student(student_id="D001", name="dorm_test", gender="M", enrollment_year=2024,
                      dept_id=dept.dept_id, class_id=cls.class_id)
        db.add(stu); db.commit()
        stu_id = stu.student_id
        db.close()
        return stu_id

    def _setup_room(self):
        from entity.base import SessionLocal
        db = SessionLocal()
        room = DormRoom(building="1号楼", room_number="101", capacity=4, gender_limit="M", occupied=0)
        db.add(room); db.commit()
        room_id = room.room_id
        db.close()
        return room_id

    def test_rooms_empty(self, svc, reset_tables):
        items, total = svc.get_rooms(page=1, page_size=10)
        assert total == 0

    def test_create_room(self, svc, reset_tables):
        room = svc.create_room({"building": "1号楼", "room_number": "101", "capacity": 4})
        assert room is not None

    def test_update_room(self, svc, reset_tables):
        room = svc.create_room({"building": "1号楼", "room_number": "101", "capacity": 4})
        updated = svc.update_room(room.room_id, {"capacity": 6, "gender_limit": "M"})
        assert updated is not None
        assert updated.capacity == 6

    def test_update_room_not_found(self, svc):
        updated = svc.update_room(9999, {"capacity": 6})
        assert updated is None

    def test_delete_room(self, svc, reset_tables):
        room = svc.create_room({"building": "1号楼", "room_number": "101", "capacity": 4})
        assert svc.delete_room(room.room_id) is True
        assert svc.delete_room(9999) is False

    def test_get_buildings(self, svc, reset_tables):
        svc.create_room({"building": "1号楼", "room_number": "101", "capacity": 4})
        svc.create_room({"building": "2号楼", "room_number": "201", "capacity": 4})
        buildings = svc.get_buildings()
        assert "1号楼" in buildings
        assert "2号楼" in buildings

    def test_get_available_rooms(self, svc, reset_tables):
        svc.create_room({"building": "1号楼", "room_number": "101", "capacity": 4})
        rooms = svc.get_available_rooms()
        assert len(rooms) == 1

    def test_checkout_nonexistent(self, svc):
        ok, msg = svc.checkout(999)
        assert ok is False

    def test_assign_and_checkout(self, svc, reset_tables):
        stu_id = self._setup_student()
        room_id = self._setup_room()
        ok, msg = svc.assign({"student_id": stu_id, "room_id": room_id, "bed_number": "A1"})
        assert ok is True
        assert msg == "分配成功"

        # check occupied updated
        assignments, total = svc.get_assignments()
        assert total == 1
        assert assignments[0].status == "在住"

        # checkout
        ok, msg = svc.checkout(assignments[0].assign_id)
        assert ok is True
        assert msg == "退宿成功"

    def test_assign_room_not_found(self, svc):
        ok, msg = svc.assign({"student_id": "X001", "room_id": 9999})
        assert ok is False
        assert "不存在" in msg

    def test_assign_room_full(self, svc, reset_tables):
        stu_id = self._setup_student()
        from entity.base import SessionLocal
        db = SessionLocal()
        room = DormRoom(building="1号楼", room_number="101", capacity=1, occupied=1)
        db.add(room); db.commit()
        room_id = room.room_id
        db.close()
        ok, msg = svc.assign({"student_id": stu_id, "room_id": room_id})
        assert ok is False
        assert "已满" in msg

    def test_assign_gender_limit(self, svc, reset_tables):
        # student F, room limit M
        from entity.base import SessionLocal
        db = SessionLocal()
        dept = Department(dept_name="测试学院")
        db.add(dept); db.flush()
        major = Major(major_name="测试专业", dept_id=dept.dept_id, duration=4)
        db.add(major); db.flush()
        cls = Class(class_name="测试班", major_id=major.major_id, enrollment_year=2024)
        db.add(cls); db.flush()
        stu = Student(student_id="D002", name="female_stu", gender="F", enrollment_year=2024,
                      dept_id=dept.dept_id, class_id=cls.class_id)
        db.add(stu); db.commit()
        stu_id = stu.student_id
        db.close()

        room_id = self._setup_room()
        ok, msg = svc.assign({"student_id": stu_id, "room_id": room_id})
        assert ok is False
        assert "性别" in msg or "仅限" in msg

    def test_assign_already_assigned(self, svc, reset_tables):
        stu_id = self._setup_student()
        room_id = self._setup_room()
        ok, msg = svc.assign({"student_id": stu_id, "room_id": room_id})
        assert ok is True
        ok2, msg2 = svc.assign({"student_id": stu_id, "room_id": room_id})
        assert ok2 is False
        assert "已有宿舍" in msg2
