# -*- coding: utf-8 -*-
"""Service 层测试 — 学生服务"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine
from service.student_service import StudentService, validate_phone, validate_email, validate_birth_date
from entity.department import Department
from entity.major import Major
from entity.class_ import Class
from entity.student import Student
from entity.teacher import Teacher
from entity.course import Course
from entity.semester import Semester
from entity.teaching import Teaching
from entity.enrollment import Enrollment
from entity.grade_scale import GradeScale

def _setup_student_fk():
    from entity.base import SessionLocal
    db = SessionLocal()
    dept = Department(dept_name="学生学院")
    db.add(dept); db.flush()
    major = Major(major_name="学生专业", dept_id=dept.dept_id, duration=4)
    db.add(major); db.flush()
    cls = Class(class_name="学生班", major_id=major.major_id, enrollment_year=2024)
    db.add(cls); db.flush()
    stu = Student(student_id="STU001", name="学生甲", gender="M", enrollment_year=2024,
                  phone="13800138001", email="stu@test.com", birth_date="2000-01-01",
                  dept_id=dept.dept_id, class_id=cls.class_id)
    db.add(stu)
    # setup for GPA test
    teacher = Teacher(teacher_id="T_STU", name="老师甲")
    db.add(teacher); db.flush()
    course = Course(course_id="C_STU", course_name="课程甲", credits=4, hours=64, type="必修")
    db.add(course); db.flush()
    sem = Semester(academic_year="2024-2025", semester_name="第一学期", start_date="2024-09-01", end_date="2025-01-15")
    db.add(sem); db.flush()
    teach = Teaching(course_id="C_STU", teacher_id="T_STU", semester_id=sem.semester_id, classroom="A101")
    db.add(teach); db.flush()
    # with score
    enroll = Enrollment(student_id="STU001", teaching_id=teach.teaching_id, score=90, grade_point=4.0, status="正常")
    db.add(enroll)
    db.commit()
    db.close()

class TestStudentService:
    @pytest.fixture
    def svc(self):
        s = StudentService()
        yield s
        s.close()

    def test_validate_phone_valid(self):
        ok, msg = validate_phone("13800138000")
        assert ok is True

    def test_validate_phone_invalid(self):
        ok, msg = validate_phone("12345")
        assert ok is False

    def test_validate_phone_empty(self):
        ok, msg = validate_phone("")
        assert ok is True

    def test_validate_email_valid(self):
        ok, msg = validate_email("test@example.com")
        assert ok is True

    def test_validate_email_invalid(self):
        ok, msg = validate_email("not-an-email")
        assert ok is False

    def test_validate_email_empty(self):
        ok, msg = validate_email("")
        assert ok is True

    def test_validate_birth_date_valid(self):
        ok, msg = validate_birth_date("2000-01-01")
        assert ok is True

    def test_validate_birth_date_invalid(self):
        ok, msg = validate_birth_date("2000/01/01")
        assert ok is False

    def test_validate_birth_date_empty(self):
        ok, msg = validate_birth_date("")
        assert ok is True

    def test_create(self, svc, reset_tables):
        _setup_student_fk()
        from entity.base import SessionLocal
        db = SessionLocal()
        dept = db.query(Department).first()
        cls = db.query(Class).first()
        db.close()
        stu = svc.create({"student_id": "STU002", "name": "学生乙", "gender": "F",
                          "enrollment_year": 2024, "dept_id": dept.dept_id, "class_id": cls.class_id})
        assert stu is not None
        assert stu.student_id == "STU002"

    def test_create_invalid_phone(self, svc, reset_tables):
        _setup_student_fk()
        from entity.base import SessionLocal
        db = SessionLocal()
        dept = db.query(Department).first()
        cls = db.query(Class).first()
        db.close()
        with pytest.raises(ValueError, match="手机号"):
            svc.create({"student_id": "STU003", "name": "学生丙", "phone": "12345",
                        "enrollment_year": 2024, "dept_id": dept.dept_id, "class_id": cls.class_id})

    def test_get_list(self, svc, reset_tables):
        _setup_student_fk()
        items, total = svc.get_list(page=1, page_size=10)
        assert total >= 1

    def test_get_list_with_keyword(self, svc, reset_tables):
        _setup_student_fk()
        items, total = svc.get_list(page=1, page_size=10, keyword="学生甲")
        assert total >= 1

    def test_get_list_with_filters(self, svc, reset_tables):
        _setup_student_fk()
        items, total = svc.get_list(page=1, page_size=10, filters={"gender": "M"})
        assert total >= 1

    def test_get_full_info(self, svc, reset_tables):
        _setup_student_fk()
        stu = svc.get_full_info("STU001")
        assert stu is not None
        assert stu.name == "学生甲"

    def test_get_full_info_not_found(self, svc, reset_tables):
        stu = svc.get_full_info("NONEXIST")
        assert stu is None

    def test_update(self, svc, reset_tables):
        _setup_student_fk()
        stu = svc.update("STU001", {"name": "新名字", "phone": "13900139001"})
        assert stu is not None
        assert stu.name == "新名字"

    def test_update_not_found(self, svc, reset_tables):
        stu = svc.update("NONEXIST", {"name": "无名"})
        assert stu is None

    def test_delete(self, svc, reset_tables):
        # Create a proper FK chain
        from entity.major import Major
        dept = Department(dept_name="测试学院")
        svc.repo.db.add(dept); svc.repo.db.flush()
        major = Major(major_name="测试专业", dept_id=dept.dept_id, duration=4)
        svc.repo.db.add(major); svc.repo.db.flush()
        cls = Class(class_name="测试班", major_id=major.major_id, enrollment_year=2024)
        svc.repo.db.add(cls); svc.repo.db.flush()
        stu = Student(student_id="DEL001", name="delete_test", enrollment_year=2024,
                      dept_id=dept.dept_id, class_id=cls.class_id)
        svc.repo.db.add(stu); svc.repo.db.commit()
        assert svc.delete("DEL001") is True
        assert svc.delete("NONEXIST") is False
    def test_get_gpa(self, svc, reset_tables):
        _setup_student_fk()
        result = svc.get_gpa("STU001")
        assert result["gpa"] == 4.0
        assert result["total_credits"] == 4

    def test_get_gpa_no_scores(self, svc, reset_tables):
        result = svc.get_gpa("NONEXIST")
        assert result["gpa"] == 0
        assert result["total_credits"] == 0

    def test_get_my_dorm(self, svc, reset_tables):
        _setup_student_fk()
        from entity.base import SessionLocal
        from entity.dorm_room import DormRoom
        from entity.dorm_assignment import DormAssignment
        from datetime import date
        db = SessionLocal()
        room = DormRoom(building="梅苑", room_number="0101", capacity=4, gender_limit="M")
        db.add(room); db.flush()
        assign = DormAssignment(student_id="STU001", room_id=room.room_id, bed_number="A",
                                check_in_date=date(2024, 9, 1), status="在住")
        db.add(assign); db.commit(); db.close()
        result = svc.get_my_dorm("STU001")
        assert len(result) == 1
        assert result[0]["building"] == "梅苑"
        assert result[0]["bed_number"] == "A"

    def test_get_my_dorm_empty(self, svc, reset_tables):
        result = svc.get_my_dorm("NOSTU")
        assert result == []
