"""选课/成绩表"""
from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, ForeignKey, func, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from entity.base import Base


class Enrollment(Base):
    __tablename__ = 'enrollments'
    __table_args__ = (UniqueConstraint('student_id', 'teaching_id'),)

    enroll_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey('students.student_id'), nullable=False)
    teaching_id = Column(Integer, ForeignKey('teaching.teaching_id'), nullable=False)
    score = Column(Numeric(5, 2))
    grade_point = Column(Numeric(3, 2))
    enroll_time = Column(DateTime, server_default=func.now())
    status = Column(String(10), default='正常')  # 正常/退课/缺考/违纪
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    student = relationship('Student', back_populates='enrollments')
    teaching = relationship('Teaching', back_populates='enrollments')
