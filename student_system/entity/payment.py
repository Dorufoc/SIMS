"""缴费表"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, TIMESTAMP, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from entity.base import Base


class Payment(Base):
    __tablename__ = 'payments'
    __table_args__ = (
        Index('idx_payment_fee_type', 'fee_type'),
        Index('idx_payment_amount_due', 'amount_due'),
        Index('idx_payment_amount_paid', 'amount_paid'),
        Index('idx_payment_payment_date', 'payment_date'),
    )

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey('students.student_id'), nullable=False)
    fee_type = Column(String(50), nullable=False)
    academic_year = Column(String(9), nullable=False)
    semester = Column(String(10))
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    payment_date = Column(Date)
    status = Column(String(10), default='未缴')  # 未缴/部分缴/已缴/退款
    payment_method = Column(String(50))
    remark = Column(Text)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    student = relationship('Student', back_populates='payments')
