# -*- coding: utf-8 -*-
"""Service 层复杂测试 — 高级查询"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine
from service.query_service import QueryService


def _setup_fk_chain():
    from entity.department import Department
    from entity.major import Major
    from entity.class_ import Class
    from entity.student import Student
    from entity.base import SessionLocal
    db = SessionLocal()
    dept = Department(dept_name="测试学院")
    db.add(dept)
    db.flush()
    major = Major(major_name="测试专业", dept_id=dept.dept_id, duration=4)
    db.add(major)
    db.flush()
    cls = Class(class_name="测试班", major_id=major.major_id, enrollment_year=2024)
    db.add(cls)
    db.flush()
    stu = Student(student_id="Q001", name="query_test", enrollment_year=2024,
                  dept_id=dept.dept_id, class_id=cls.class_id)
    db.add(stu)
    # add another student
    stu2 = Student(student_id="Q002", name="extra_student", enrollment_year=2024,
                   dept_id=dept.dept_id, class_id=cls.class_id, gender="M")
    db.add(stu2)
    db.commit()
    db.close()


class TestQueryService:
    @pytest.fixture
    def svc(self):
        s = QueryService()
        yield s
        s.close()

    def test_dynamic_query_empty(self, svc, reset_tables):
        results = svc.dynamic_query([])
        assert results is not None

    def test_dynamic_query_with_conditions(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "student_id", "operator": "=", "value": "Q001", "logic": "AND"}
        ])
        assert len(results) == 1

    def test_dynamic_query_like(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "name", "operator": "LIKE", "value": "query", "logic": "AND"}
        ])
        assert len(results) == 1

    def test_dynamic_query_neq(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "student_id", "operator": "!=", "value": "Q001", "logic": "AND"}
        ])
        assert len(results) == 1
        assert results[0].student_id == "Q002"

    def test_dynamic_query_not_in(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "student_id", "operator": "NOT_IN", "value": "Q001", "logic": "AND"}
        ])
        assert len(results) == 1

    def test_dynamic_query_is_null(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "phone", "operator": "IS_NULL", "value": "", "logic": "AND"}
        ])
        assert len(results) == 2

    def test_dynamic_query_is_not_null(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "gender", "operator": "IS_NOT_NULL", "value": "", "logic": "AND"}
        ])
        assert len(results) == 1

    def test_dynamic_query_not_flag(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "student_id", "operator": "=", "value": "Q001", "not": True, "logic": "AND"}
        ])
        assert len(results) == 1
        assert results[0].student_id == "Q002"

    def test_dynamic_query_or_logic(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "student_id", "operator": "=", "value": "Q001", "logic": "AND"},
            {"field": "student_id", "operator": "=", "value": "Q002", "logic": "OR"},
        ])
        assert len(results) == 2

    def test_dynamic_query_gt(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "enrollment_year", "operator": ">", "value": "2023", "logic": "AND"}
        ])
        assert len(results) == 2

    def test_dynamic_query_gte(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "enrollment_year", "operator": ">=", "value": "2024", "logic": "AND"}
        ])
        assert len(results) == 2

    def test_dynamic_query_lt(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "enrollment_year", "operator": "<", "value": "2025", "logic": "AND"}
        ])
        assert len(results) == 2

    def test_dynamic_query_lte(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "enrollment_year", "operator": "<=", "value": "2024", "logic": "AND"}
        ])
        assert len(results) == 2

    def test_dynamic_query_in(self, svc, reset_tables):
        _setup_fk_chain()
        results = svc.dynamic_query([
            {"field": "student_id", "operator": "IN", "value": "Q001,Q002", "logic": "AND"}
        ])
        assert len(results) == 2

    def test_sort_query(self, svc, reset_tables):
        _setup_fk_chain()
        items, total = svc.sort_query([{"field": "student_id", "order": "asc"}], page=1, page_size=10)
        assert total >= 2

    def test_sort_query_desc(self, svc, reset_tables):
        _setup_fk_chain()
        items, total = svc.sort_query([{"field": "student_id", "order": "desc"}], page=1, page_size=10)
        assert total >= 2

    def test_sort_query_multi_field(self, svc, reset_tables):
        _setup_fk_chain()
        items, total = svc.sort_query([
            {"field": "dept_name", "order": "asc"},
            {"field": "student_id", "order": "desc"},
        ], page=1, page_size=10)
        assert total >= 2

    def test_allowed_fields(self):
        from service.query_service import ALLOWED_FIELDS
        assert "student_id" in ALLOWED_FIELDS
        assert "name" in ALLOWED_FIELDS
