"""课程表"""
from sqlalchemy import Column, String, Integer, SmallInteger, TIMESTAMP, ForeignKey, func, Numeric
from sqlalchemy.orm import relationship
from entity.base import Base


class Course(Base):
    __tablename__ = 'courses'

    course_id = Column(String(20), primary_key=True)
    course_name = Column(String(100), nullable=False)
    credits = Column(Numeric(3, 1), nullable=False)
    hours = Column(SmallInteger)
    type = Column(String(10), nullable=False)  # 必修/选修/公共
    dept_id = Column(Integer, ForeignKey('departments.dept_id'))
    created_at = Column(TIMESTAMP, server_default=func.now())

    department = relationship('Department', back_populates='courses')
    teachings = relationship('Teaching', back_populates='course', lazy='dynamic')
    curricula = relationship('Curriculum', back_populates='course', lazy='dynamic')
