"""用户表"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, DateTime, Boolean, func, Index
from sqlalchemy.orm import relationship
from entity.base import Base


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_user_created_at', 'created_at'),
    )

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False)  # admin/teacher/student
    ref_id = Column(String(20))
    real_name = Column(String(50), nullable=True, comment='真实姓名')
    email = Column(String(100))
    phone = Column(String(20))
    last_login = Column(DateTime)
    username_changed = Column(Boolean, default=False, comment='是否已完成用户名修改')
    created_at = Column(TIMESTAMP, server_default=func.now())

    permissions = relationship('UserPermission', back_populates='user', lazy='dynamic')
