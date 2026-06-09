# -*- coding: utf-8 -*-
"""Service 层测试 — 选课服务"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine
from service.enrollment_service import EnrollmentService
from entity.department import Department
from entity.major import Major
from entity.class_ import Class
from entity.student import Student
from entity.teacher import Teacher
from entity.course import Course
from entity.semester import Semester
from entity.teaching import Teaching
from entity.enrollment import Enrollment

def _setup_full_chain():
    db = SessionLocal()
    dept = Department(dept_name="测试学院")
    db.add(dept); db.flush()
    major = Major(major_name="测试专业", dept_id=dept.dept_id, duration=4)
    db.add(major); db.flush()
    cls = Class(class_name="测试班", major_id=major.major_id, enrollment_year=2024)
    db.add(cls); db.flush()
    stu = Student(student_id="E001", name="enroll_test", enrollment_year=2024,
                  dept_id=dept.dept_id, class_id=cls.class_id)
    db.add(stu); db.flush()
    teacher = Teacher(teacher_id="T_E01", name="陈老师")
    db.add(teacher); db.flush()
    course = Course(course_id="E_C01", course_name="高等数学", credits=4, hours=64, type="必修")
    db.add(course); db.flush()
    sem = Semester(academic_year="2024-2025", semester_name="第一学期", start_date="2024-09-01", end_date="2025-01-15")
    db.add(sem); db.flush()
    teach = Teaching(course_id="E_C01", teacher_id="T_E01", semester_id=sem.semester_id,
                     classroom="A101", schedule="周一 1-2节", capacity=60)
    db.add(teach); db.commit()
    tid = teach.teaching_id
    db.close()
    return "E001", tid

from entity.base import SessionLocal

class TestEnrollmentService:
    @pytest.fixture
    def svc(self):
        s = EnrollmentService()
        yield s
        s.close()

    def test_get_available_courses(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        courses = svc.get_available_courses(stu_id)
        assert len(courses) == 1

    def test_enroll_success(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        ok, msg = svc.enroll(stu_id, tid)
        assert ok is True
        assert "成功" in msg

    def test_enroll_duplicate(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        svc.enroll(stu_id, tid)
        ok, msg = svc.enroll(stu_id, tid)
        assert ok is False
        assert "已选" in msg

    def test_enroll_course_not_found(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        ok, msg = svc.enroll(stu_id, 9999)
        assert ok is False
        assert "不存在" in msg

    def test_drop_success(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        ok, msg = svc.enroll(stu_id, tid)
        assert ok is True
        # find enrollment
        from entity.base import SessionLocal
        db = SessionLocal()
        enroll = db.query(Enrollment).filter(Enrollment.student_id == stu_id).first()
        eid = enroll.enroll_id
        db.close()
        ok, msg = svc.drop(eid)
        assert ok is True
        assert "退课成功" in msg

    def test_drop_not_found(self, svc):
        ok, msg = svc.drop(9999)
        assert ok is False

    def test_get_student_enrollments(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        svc.enroll(stu_id, tid)
        enrollments = svc.get_student_enrollments(stu_id)
        assert len(enrollments) == 1

    def test_reenroll_after_drop(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        svc.enroll(stu_id, tid)
        from entity.base import SessionLocal
        db = SessionLocal()
        enroll = db.query(Enrollment).filter(Enrollment.student_id == stu_id).first()
        eid = enroll.enroll_id
        db.close()
        svc.drop(eid)
        ok, msg = svc.enroll(stu_id, tid)
        assert ok is True
        assert "重新选课" in msg

    def test_enroll_capacity_full(self, svc, reset_tables):
        stu_id, tid = _setup_full_chain()
        # set capacity to 0
        from entity.base import SessionLocal
        db = SessionLocal()
        teach = db.query(Teaching).filter(Teaching.teaching_id == tid).first()
        teach.capacity = 0
        db.commit()
        db.close()
        ok, msg = svc.enroll(stu_id, tid)
        assert ok is False
        assert "已满" in msg
