"""院系表"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from entity.base import Base


class Department(Base):
    __tablename__ = 'departments'

    dept_id = Column(Integer, primary_key=True, autoincrement=True)
    dept_name = Column(String(100), unique=True, nullable=False)
    dean = Column(String(50))
    phone = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now())

    majors = relationship('Major', back_populates='department', lazy='dynamic')
    teachers = relationship('Teacher', back_populates='department', lazy='dynamic')
    courses = relationship('Course', back_populates='department', lazy='dynamic')
