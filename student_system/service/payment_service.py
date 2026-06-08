"""缴费服务"""
from repository.payment_repo import PaymentRepo
from entity.payment import Payment
from datetime import date


class PaymentService:
    def __init__(self):
        self.repo = PaymentRepo()

    def close(self):
        self.repo.close()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Payment.payment_id.desc())

    def create(self, data: dict):
        return self.repo.create(Payment(**data))

    def pay(self, payment_id: int, amount: float, method: str = ''):
        """登记缴费"""
        if amount <= 0:
            return False, '缴费金额必须大于0'

        payment = self.repo.get_by_id(payment_id)
        if not payment:
            return False, '缴费记录不存在'

        payment.amount_paid = (payment.amount_paid or 0) + amount
        payment.payment_date = date.today()
        if payment.amount_paid >= payment.amount_due:
            payment.status = '已缴'
        else:
            payment.status = '部分缴'
        if method:
            payment.payment_method = method
        self.repo.db.commit()
        return True, '缴费登记成功'

    def get_overdue(self):
        """获取欠费学生列表"""
        return self.repo.db.query(Payment).filter(
            Payment.status.in_(['未缴', '部分缴'])
        ).order_by(Payment.student_id).all()

    def get_stats(self):
        """缴费统计"""
        from sqlalchemy import func
        total_due = self.repo.db.query(func.sum(Payment.amount_due)).scalar() or 0
        total_paid = self.repo.db.query(func.sum(Payment.amount_paid)).scalar() or 0
        count = self.repo.count()
        return {
            'total_due': float(total_due),
            'total_paid': float(total_paid),
            'unpaid': float(total_due) - float(total_paid),
            'count': count,
        }
