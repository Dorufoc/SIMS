"""教室表"""
from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, func, Index
from entity.base import Base


class Classroom(Base):
    __tablename__ = 'classrooms'
    __table_args__ = (
        Index('idx_classroom_floor', 'floor'),
    )

    classroom_id = Column(Integer, primary_key=True, autoincrement=True)
    classroom_name = Column(String(50), nullable=False, comment='教室名称/编号，如 A101')
    building = Column(String(50), comment='所属楼栋')
    floor = Column(SmallInteger, comment='楼层')
    capacity = Column(SmallInteger, default=30, comment='容纳人数')
    type = Column(String(20), default='普通教室', comment='教室类型：普通教室/多媒体教室/实验室/机房')
    created_at = Column(TIMESTAMP, server_default=func.now())
