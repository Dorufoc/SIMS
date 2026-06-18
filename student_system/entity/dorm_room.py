"""宿舍房间表"""
from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, func, Index
from sqlalchemy.orm import relationship
from entity.base import Base


class DormRoom(Base):
    __tablename__ = 'dorm_rooms'
    __table_args__ = (
        Index('idx_dorm_room_capacity', 'capacity'),
        Index('idx_dorm_room_occupied', 'occupied'),
    )

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    building = Column(String(50), nullable=False)
    room_number = Column(String(20), nullable=False)
    capacity = Column(SmallInteger, nullable=False)
    occupied = Column(SmallInteger, default=0)
    gender_limit = Column(String(10), default='不限')  # M/F/不限
    phone = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now())

    assignments = relationship('DormAssignment', back_populates='room', lazy='dynamic')
