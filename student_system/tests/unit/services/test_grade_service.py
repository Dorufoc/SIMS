# -*- coding: utf-8 -*-
"""测试成绩服务"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine

from service.grade_service import GradeService
from entity.grade_scale import GradeScale
from entity.enrollment import Enrollment
from entity.teaching import Teaching
from entity.course import Course
from entity.teacher import Teacher
from entity.semester import Semester
from entity.student import Student
from entity.department import Department
from entity.major import Major
from entity.class_ import Class

class TestGradeService:
    @pytest.fixture
    def svc(self):
        s = GradeService()
        yield s
        s.close()

    def _init_grade_scale(self):
        from entity.base import SessionLocal
        db = SessionLocal()
        scales = [
            GradeScale(grade_level="A", min_score=90, max_score=100, grade_point=4.0),
            GradeScale(grade_level="B", min_score=80, max_score=89, grade_point=3.0),
            GradeScale(grade_level="C", min_score=70, max_score=79, grade_point=2.0),
            GradeScale(grade_level="D", min_score=60, max_score=69, grade_point=1.0),
            GradeScale(grade_level="F", min_score=0, max_score=59, grade_point=0.0),
        ]
        for s in scales:
            db.add(s)
        db.commit()
        db.close()

    def _setup_enrollment(self):
        from entity.base import SessionLocal
        db = SessionLocal()
        dept = Department(dept_name="测试学院")
        db.add(dept); db.flush()
        major = Major(major_name="测试专业", dept_id=dept.dept_id, duration=4)
        db.add(major); db.flush()
        cls = Class(class_name="测试班", major_id=major.major_id, enrollment_year=2024)
        db.add(cls); db.flush()
        stu = Student(student_id="G001", name="grade_test", enrollment_year=2024,
                      dept_id=dept.dept_id, class_id=cls.class_id)
        db.add(stu); db.flush()
        teacher = Teacher(teacher_id="T001", name="张老师")
        db.add(teacher); db.flush()
        course = Course(course_id="C001", course_name="数学", credits=4, hours=64, type="必修")
        db.add(course); db.flush()
        sem = Semester(academic_year="2024-2025", semester_name="第一学期", start_date="2024-09-01", end_date="2025-01-15")
        db.add(sem); db.flush()
        teach = Teaching(course_id="C001", teacher_id="T001", semester_id=sem.semester_id, classroom="A101")
        db.add(teach); db.flush()
        enroll = Enrollment(student_id="G001", teaching_id=teach.teaching_id, status="正常")
        db.add(enroll); db.commit()
        eid = enroll.enroll_id
        tid = teach.teaching_id
        db.close()
        return eid, tid, "G001"

    def test_calc_grade_point(self, svc, reset_tables):
        self._init_grade_scale()
        assert svc._calc_grade_point(95) == 4.0
        assert svc._calc_grade_point(85) == 3.0
        assert svc._calc_grade_point(75) == 2.0
        assert svc._calc_grade_point(65) == 1.0
        assert svc._calc_grade_point(50) == 0.0
        assert svc._calc_grade_point(0) == 0.0
        assert svc._calc_grade_point(None) == 0.0

    def test_set_score_success(self, svc, reset_tables):
        self._init_grade_scale()
        eid, tid, sid = self._setup_enrollment()
        ok, msg = svc.set_score(eid, 85)
        assert ok is True
        assert msg == "成绩录入成功"

    def test_set_score_not_found(self, svc, reset_tables):
        self._init_grade_scale()
        ok, msg = svc.set_score(9999, 85)
        assert ok is False
        assert msg == "选课记录不存在"

    def test_set_score_invalid_score(self, svc, reset_tables):
        self._init_grade_scale()
        eid, tid, sid = self._setup_enrollment()
        ok, msg = svc.set_score(eid, "abc")
        assert ok is False
        assert msg == "成绩格式不正确"

    def test_batch_score(self, svc, reset_tables):
        self._init_grade_scale()
        eid, tid, sid = self._setup_enrollment()
        ok, msg = svc.batch_score([{"enroll_id": eid, "score": 90}])
        assert ok is True
        assert "批量录入完成" in msg

    def test_get_teaching_students(self, svc, reset_tables):
        self._init_grade_scale()
        eid, tid, sid = self._setup_enrollment()
        students = svc.get_teaching_students(tid)
        assert len(students) == 1

    def test_get_student_scores(self, svc, reset_tables):
        self._init_grade_scale()
        eid, tid, sid = self._setup_enrollment()
        svc.set_score(eid, 85)
        scores = svc.get_student_scores("G001")
        assert len(scores) == 1
        assert float(scores[0].score) == 85.0

    def test_get_course_score_stats_with_data(self, svc, reset_tables):
        self._init_grade_scale()
        eid, tid, sid = self._setup_enrollment()
        svc.set_score(eid, 85)
        stats = svc.get_course_score_stats(tid)
        assert stats["avg"] == 85.0
        assert stats["max"] == 85.0
        assert stats["min"] == 85.0
        assert stats["count"] == 1

    def test_get_course_score_stats_empty(self, svc, reset_tables):
        eid, tid, sid = self._setup_enrollment()
        stats = svc.get_course_score_stats(tid)
        assert stats["avg"] == 0
        assert stats["count"] == 0
