# -*- coding: utf-8 -*-
"""Service 层测试 — 统计服务"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine
from service.statistics_service import StatisticsService
from entity.department import Department
from entity.major import Major
from entity.class_ import Class
from entity.student import Student
from entity.enrollment import Enrollment
from entity.teacher import Teacher
from entity.course import Course
from entity.semester import Semester
from entity.teaching import Teaching
from entity.grade_scale import GradeScale

def _setup_stat_fk():
    from entity.base import SessionLocal
    db = SessionLocal()
    dept = Department(dept_name="统计学院")
    db.add(dept); db.flush()
    major = Major(major_name="统计学", dept_id=dept.dept_id, duration=4)
    db.add(major); db.flush()
    cls = Class(class_name="统计班", major_id=major.major_id, enrollment_year=2024)
    db.add(cls); db.flush()
    stu = Student(student_id="S001", name="stat_test", enrollment_year=2024, gender="M",
                  status="在校", dept_id=dept.dept_id, class_id=cls.class_id)
    db.add(stu); db.flush()
    scales = [
        GradeScale(grade_level="A", min_score=90, max_score=100, grade_point=4.0),
        GradeScale(grade_level="B", min_score=80, max_score=89, grade_point=3.0),
    ]
    for s in scales:
        db.add(s)
    teacher = Teacher(teacher_id="T_STAT", name="统计老师")
    db.add(teacher); db.flush()
    course = Course(course_id="C_STAT", course_name="统计课", credits=4, hours=64, type="必修")
    db.add(course); db.flush()
    sem = Semester(academic_year="2024-2025", semester_name="第一学期", start_date="2024-09-01", end_date="2025-01-15")
    db.add(sem); db.flush()
    teach = Teaching(course_id="C_STAT", teacher_id="T_STAT", semester_id=sem.semester_id, classroom="A101")
    db.add(teach); db.flush()
    enroll = Enrollment(student_id="S001", teaching_id=teach.teaching_id, score=85, grade_point=3.0, status="正常")
    db.add(enroll)
    enroll2 = Enrollment(student_id="S001", status="正常")
    # Enrollment needs a teaching_id
    teach2 = Teaching(course_id="C_STAT", teacher_id="T_STAT", semester_id=sem.semester_id, classroom="A102")
    db.add(teach2); db.flush()
    enroll2.teaching_id = teach2.teaching_id
    enroll2.score = None
    enroll2.grade_point = None
    db.add(enroll2)
    db.commit()
    db.close()


def _setup_age_student():
    """创建一条带出生日期的学生记录，用于年龄相关统计"""
    from entity.base import SessionLocal
    from datetime import date
    db = SessionLocal()
    dept = Department(dept_name="年龄学院")
    db.add(dept); db.flush()
    major = Major(major_name="年龄专业", dept_id=dept.dept_id, duration=4)
    db.add(major); db.flush()
    cls = Class(class_name="年龄班", major_id=major.major_id, enrollment_year=2024)
    db.add(cls); db.flush()
    stu = Student(student_id="SAGE001", name="年龄测试", enrollment_year=2024, gender="M",
                  birth_date=date(2000, 1, 1), status="在校",
                  dept_id=dept.dept_id, class_id=cls.class_id)
    db.add(stu)
    db.commit()
    db.close()

class TestStatisticsService:
    @pytest.fixture
    def svc(self):
        s = StatisticsService()
        yield s
        s.close()

    def test_dashboard_zero(self, svc, reset_tables):
        d = svc.dashboard()
        assert d["student_count"] == 0

    def test_dashboard_with_data(self, svc, reset_tables):
        _setup_stat_fk()
        d = svc.dashboard()
        assert d["student_count"] >= 1

    def test_student_by_dept(self, svc, reset_tables):
        _setup_stat_fk()
        rows = svc.student_by_dept()
        assert len(rows) >= 1

    def test_student_by_major(self, svc, reset_tables):
        _setup_stat_fk()
        rows = svc.student_by_major()
        assert len(rows) >= 1

    def test_student_by_class(self, svc, reset_tables):
        _setup_stat_fk()
        rows = svc.student_by_class()
        assert len(rows) >= 1

    def test_student_by_enrollment_year(self, svc, reset_tables):
        _setup_stat_fk()
        rows = svc.student_by_enrollment_year()
        assert len(rows) >= 1

    def test_gender_distribution(self, svc, reset_tables):
        _setup_stat_fk()
        rows = svc.gender_distribution()
        assert len(rows) >= 1

    def test_student_status(self, svc, reset_tables):
        _setup_stat_fk()
        rows = svc.student_status()
        assert len(rows) >= 1

    def test_grade_distribution_no_data(self, svc, reset_tables):
        result = svc.grade_distribution()
        assert result["total"] == 0
        assert result["avg"] == 0

    def test_grade_distribution_with_data(self, svc, reset_tables):
        _setup_stat_fk()
        result = svc.grade_distribution()
        assert result["total"] >= 1
        assert result["avg"] > 0

    def test_gpa_ranking_no_data(self, svc, reset_tables):
        result = svc.gpa_ranking()
        assert len(result) == 0

    def test_gpa_ranking_with_data(self, svc, reset_tables):
        _setup_stat_fk()
        result = svc.gpa_ranking()
        assert len(result) >= 1

    def test_class_grade_stats(self, svc, reset_tables):
        _setup_stat_fk()
        result = svc.class_grade_stats()
        assert len(result) >= 1
        assert result[0]["avg_score"] is not None

    def test_class_grade_stats_by_semester(self, svc, reset_tables):
        _setup_stat_fk()
        from entity.base import SessionLocal
        db = SessionLocal()
        sem = db.query(Semester).first()
        db.close()
        result = svc.class_grade_stats(semester_id=sem.semester_id)
        assert len(result) >= 1

    def test_age_stats_by_major(self, svc, reset_tables):
        _setup_age_student()
        result = svc.age_stats_by_major()
        assert len(result) >= 1
        assert result[0]["max_age"] >= result[0]["min_age"]

    def test_grade_avg_age(self, svc, reset_tables):
        _setup_age_student()
        result = svc.grade_avg_age()
        assert len(result) >= 1
        assert result[0]["grade"] == "2024"
        assert result[0]["avg_age"] > 0

    def test_age_range_stats(self, svc, reset_tables):
        _setup_age_student()
        result = svc.age_range_stats(10, 100)
        assert result["count"] >= 1

    def test_age_range_stats_no_match(self, svc, reset_tables):
        _setup_age_student()
        result = svc.age_range_stats(1, 5)
        assert result["count"] == 0

    def test_student_count_with_birth_date(self, svc, reset_tables):
        _setup_age_student()
        count = svc.student_count_with_birth_date()
        assert count >= 1

    def test_student_count_with_birth_date_empty(self, svc, reset_tables):
        assert svc.student_count_with_birth_date() == 0
