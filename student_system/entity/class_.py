"""班级表"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from entity.base import Base


class Class(Base):  # 文件名 class_.py，类名 Class
    __tablename__ = 'classes'

    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(50), nullable=False)
    major_id = Column(Integer, ForeignKey('majors.major_id'), nullable=False)
    enrollment_year = Column(Integer, nullable=False)
    advisor = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    major = relationship('Major', back_populates='classes')
    teacher = relationship('Teacher', foreign_keys='Class.advisor', primaryjoin='Class.advisor == Teacher.teacher_id')
    students = relationship('Student', back_populates='class_', lazy='dynamic')
