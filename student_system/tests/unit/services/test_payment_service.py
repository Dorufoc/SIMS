# -*- coding: utf-8 -*-
"""Service 层复杂测试 — 缴费"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
from entity.base import Base, engine
from service.payment_service import PaymentService
from service.student_service import StudentService


class TestPaymentService:
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
        # 创建测试学生（Payment 有 FK -> students.student_id）
        stu_svc = StudentService()
        stu_svc.create({"student_id": "S001", "name": "测试学生", "enrollment_year": 2024})
        stu_svc.close()
        yield

    @pytest.fixture
    def svc(self, setup):
        s = PaymentService()
        yield s
        s.close()

    def test_create_and_pay(self, svc):
        pay = svc.create({"student_id": "S001", "fee_type": "学费", "amount_due": 5000,
                          "academic_year": "2024-2025", "semester": "第一学期"})
        assert pay is not None
        ok, msg = svc.pay(pay.payment_id, 5000)
        assert ok is True

    def test_pay_nonexistent(self, svc):
        ok, msg = svc.pay(999, 5000)
        assert ok is False

    def test_pay_negative(self, svc):
        ok, msg = svc.pay(999, -100)
        assert ok is False

    def test_get_overdue(self, svc):
        overdue = svc.get_overdue()
        assert overdue is not None

    def test_get_stats_zero(self, svc):
        stats = svc.get_stats()
        assert stats["count"] == 0
        assert stats["total_due"] == 0
