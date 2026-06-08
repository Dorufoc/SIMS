"""奖惩表"""
from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from entity.base import Base


class RewardPunishment(Base):
    __tablename__ = 'rewards_punishments'

    rp_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey('students.student_id'), nullable=False)
    rp_type = Column(String(10), nullable=False)  # 奖励/处分
    title = Column(String(100), nullable=False)
    level = Column(String(50))
    date = Column(Date, nullable=False)
    reason = Column(Text)
    issuing_authority = Column(String(100))
    remark = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship('Student', back_populates='rewards_punishments')
