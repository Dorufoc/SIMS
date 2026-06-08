"""教师表"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from entity.base import Base


class Teacher(Base):
    __tablename__ = 'teachers'

    teacher_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(1))
    title = Column(String(50))
    dept_id = Column(Integer, ForeignKey('departments.dept_id'))
    phone = Column(String(20))
    email = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    department = relationship('Department', back_populates='teachers')
    teachings = relationship('Teaching', back_populates='teacher', lazy='dynamic')
