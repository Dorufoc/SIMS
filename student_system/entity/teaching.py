"""授课表"""
from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from entity.base import Base


class Teaching(Base):
    __tablename__ = 'teaching'
    __table_args__ = (
        Index('idx_teaching_schedule', 'schedule'),
        Index('idx_teaching_classroom', 'classroom'),
        Index('idx_teaching_capacity', 'capacity'),
    )

    teaching_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String(20), ForeignKey('courses.course_id'), nullable=False)
    teacher_id = Column(String(20), ForeignKey('teachers.teacher_id'), nullable=False)
    semester_id = Column(Integer, ForeignKey('semesters.semester_id'), nullable=False)
    classroom = Column(String(50))
    schedule = Column(String(200))
    capacity = Column(SmallInteger, default=30)
    created_at = Column(TIMESTAMP, server_default=func.now())

    course = relationship('Course', back_populates='teachings')
    teacher = relationship('Teacher', back_populates='teachings')
    semester = relationship('Semester', back_populates='teachings')
    enrollments = relationship('Enrollment', back_populates='teaching', lazy='dynamic')
