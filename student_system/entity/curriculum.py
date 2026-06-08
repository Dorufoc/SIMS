"""培养计划表"""
from sqlalchemy import Column, Integer, String, SmallInteger, Boolean, Text, TIMESTAMP, ForeignKey, func, Numeric
from sqlalchemy.orm import relationship
from entity.base import Base


class Curriculum(Base):
    __tablename__ = 'curriculum'

    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    major_id = Column(Integer, ForeignKey('majors.major_id'), nullable=False)
    enrollment_year = Column(Integer, nullable=False)
    course_id = Column(String(20), ForeignKey('courses.course_id'), nullable=False)
    course_type = Column(String(10), default='必修')  # 必修/选修/公共
    recommended_term = Column(String(20))
    min_grade = Column(Numeric(4, 1))
    is_core = Column(Boolean, default=False)
    remark = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    major = relationship('Major', back_populates='curricula')
    course = relationship('Course', back_populates='curricula')
