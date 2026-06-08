"""选课日志表"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from entity.base import Base


class EnrollLog(Base):
    __tablename__ = 'enroll_logs'

    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey('students.student_id'), nullable=False)
    teaching_id = Column(Integer, ForeignKey('teaching.teaching_id'), nullable=False)
    operation_type = Column(String(10))  # 选课/退课/成绩修改/状态变更
    old_value = Column(Text)
    new_value = Column(Text)
    operator = Column(String(50))
    operator_ip = Column(String(45))
    reason = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship('Student', back_populates='enroll_logs')
    teaching = relationship('Teaching', back_populates='enroll_logs')
