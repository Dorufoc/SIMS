"""用户权限表"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from entity.base import Base


class UserPermission(Base):
    __tablename__ = 'user_permissions'

    perm_id = Column(Integer, primary_key=True, autoincrement=True)
    user_uuid = Column(String(36), ForeignKey('users.uuid'), nullable=False)
    table_name = Column(String(100), nullable=False)
    permission_code = Column(String(10), default='000')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship('User', back_populates='permissions')
