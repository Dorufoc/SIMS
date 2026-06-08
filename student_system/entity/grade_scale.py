"""成绩等级表"""
from sqlalchemy import Column, String, Numeric
from entity.base import Base


class GradeScale(Base):
    __tablename__ = 'grade_scale'

    grade_level = Column(String(1), primary_key=True)
    min_score = Column(Numeric(5, 2), nullable=False)
    max_score = Column(Numeric(5, 2), nullable=False)
    grade_point = Column(Numeric(3, 2), nullable=False)
    description = Column(String(50))
