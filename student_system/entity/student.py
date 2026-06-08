"""学生表"""
from sqlalchemy import Column, String, Date, Integer, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from entity.base import Base


class Student(Base):
    __tablename__ = 'students'

    student_id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(1))  # 'M' or 'F'
    birth_date = Column(Date)
    id_card_no = Column(String(18), unique=True)
    enrollment_year = Column(Integer, nullable=False)
    dept_id = Column(Integer, ForeignKey('departments.dept_id'))
    class_id = Column(Integer, ForeignKey('classes.class_id'))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(200))
    status = Column(String(10), default='在校')  # 在校/休学/毕业/退学
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    department = relationship('Department')
    class_ = relationship('Class', back_populates='students')
    enrollments = relationship('Enrollment', back_populates='student', lazy='dynamic')
    rewards_punishments = relationship('RewardPunishment', back_populates='student', lazy='dynamic')
    payments = relationship('Payment', back_populates='student', lazy='dynamic')
    dorm_assignments = relationship('DormAssignment', back_populates='student', lazy='dynamic')
    enroll_logs = relationship('EnrollLog', back_populates='student', lazy='dynamic')
