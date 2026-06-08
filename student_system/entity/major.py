"""专业表"""
from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from entity.base import Base


class Major(Base):
    __tablename__ = 'majors'

    major_id = Column(Integer, primary_key=True, autoincrement=True)
    major_name = Column(String(100), nullable=False)
    dept_id = Column(Integer, ForeignKey('departments.dept_id'), nullable=False)
    duration = Column(SmallInteger, default=4)
    created_at = Column(TIMESTAMP, server_default=func.now())

    department = relationship('Department', back_populates='majors')
    classes = relationship('Class', back_populates='major', lazy='dynamic')
    curricula = relationship('Curriculum', back_populates='major', lazy='dynamic')
