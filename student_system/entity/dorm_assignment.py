"""住宿分配表"""
from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from entity.base import Base


class DormAssignment(Base):
    __tablename__ = 'dorm_assignments'
    __table_args__ = (UniqueConstraint('room_id', 'bed_number'),)

    assign_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey('students.student_id'), nullable=False)
    room_id = Column(Integer, ForeignKey('dorm_rooms.room_id'), nullable=False)
    bed_number = Column(String(10))
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date)
    status = Column(String(10), default='在住')  # 在住/已退/调换
    remark = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship('Student', back_populates='dorm_assignments')
    room = relationship('DormRoom', back_populates='assignments')
