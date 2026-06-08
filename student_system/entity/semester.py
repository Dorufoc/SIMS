"""学期表"""
from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from entity.base import Base


class Semester(Base):
    __tablename__ = 'semesters'

    semester_id = Column(Integer, primary_key=True, autoincrement=True)
    academic_year = Column(String(9), nullable=False)  # e.g. '2024-2025'
    semester_name = Column(String(10), nullable=False)  # e.g. '第一学期'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    teachings = relationship('Teaching', back_populates='semester', lazy='dynamic')
