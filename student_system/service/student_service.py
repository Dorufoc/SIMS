"""学生服务"""
import re
from datetime import datetime
from repository.student_repo import StudentRepo
from repository.base import escape_like
from entity.student import Student
from sqlalchemy.orm import joinedload


def validate_phone(phone):
    """验证手机号格式 (中国大陆)"""
    if phone and not re.match(r'^1[3-9]\d{9}$', phone):
        return False, '手机号格式不正确'
    return True, ''


def validate_email(email):
    """验证邮箱格式"""
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, '邮箱格式不正确'
    return True, ''


def validate_birth_date(date_str):
    """验证日期格式 YYYY-MM-DD"""
    if not date_str:
        return True, ''
    try:
        datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
        return True, ''
    except ValueError:
        return False, '出生日期格式不正确'


class StudentService:
    def __init__(self):
        self.repo = StudentRepo()

    def close(self):
        self.repo.close()

    def get_list(self, page=1, page_size=10, filters=None, keyword=None):
        """获取学生列表（带筛选和搜索）"""
        from entity.class_ import Class
        from entity.major import Major
        from entity.department import Department

        q = self.repo.db.query(Student).options(
            joinedload(Student.class_).joinedload(Class.major).joinedload(Major.department)
        )

        if filters:
            # 手动构建筛选条件以保持 joinedload
            from sqlalchemy import and_
            for k, v in filters.items():
                if v is not None:
                    col = getattr(Student, k, None)
                    if col is not None:
                        q = q.filter(col == v)

        if keyword:
            escaped = escape_like(keyword)
            q = q.filter(
                (Student.student_id.like(f'%{escaped}%', escape='\\')) |
                (Student.name.like(f'%{escaped}%', escape='\\')) |
                (Student.phone.like(f'%{escaped}%', escape='\\'))
            )

        q = q.order_by(Student.student_id)
        return self.repo.paginate(page, page_size, q)

    def get_full_info(self, student_id):
        """获取学生完整信息包含关联"""
        from entity.class_ import Class
        from entity.major import Major
        from entity.department import Department

        return self.repo.db.query(Student).options(
            joinedload(Student.class_).joinedload(Class.major).joinedload(Major.department)
        ).filter(Student.student_id == student_id).first()

    def create(self, data: dict):
        """创建学生"""
        # 验证
        phone = data.get('phone', '')
        email = data.get('email', '')
        birth_date = data.get('birth_date', '')
        ok, err = validate_phone(phone)
        if not ok: raise ValueError(err)
        ok, err = validate_email(email)
        if not ok: raise ValueError(err)
        ok, err = validate_birth_date(str(birth_date) if birth_date else '')
        if not ok: raise ValueError(err)

        # 检查学号唯一性
        student_id = data.get('student_id')
        if student_id:
            existing = self.repo.get_by_id(student_id)
            if existing:
                raise ValueError(f'学号 {student_id} 已存在')

        # 验证学院-专业-班级的层级关系
        class_id = data.get('class_id')
        dept_id = data.get('dept_id')
        if class_id:
            from entity.class_ import Class
            cls = self.repo.db.query(Class).filter(Class.class_id == class_id).first()
            if not cls:
                raise ValueError('所选班级不存在')
            if dept_id and cls.major.dept_id != dept_id:
                raise ValueError('所选班级不属于所选学院')
            # 将 dept_id 设置为班级所属专业的学院，确保数据一致性
            data['dept_id'] = cls.major.dept_id

        student = Student(**data)
        return self.repo.create(student)

    def update(self, student_id: str, data: dict):
        """更新学生"""
        ALLOWED_FIELDS = {'name', 'gender', 'birth_date', 'enrollment_year',
                         'dept_id', 'class_id', 'phone', 'email', 'address', 'status'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        
        # 验证
        phone = filtered_data.get('phone', '')
        email = filtered_data.get('email', '')
        birth_date = filtered_data.get('birth_date', '')
        if phone:
            ok, err = validate_phone(str(phone))
            if not ok: raise ValueError(err)
        if email:
            ok, err = validate_email(str(email))
            if not ok: raise ValueError(err)
        if birth_date:
            ok, err = validate_birth_date(str(birth_date))
            if not ok: raise ValueError(err)

        # 验证学院-专业-班级的层级关系
        class_id = filtered_data.get('class_id')
        dept_id = filtered_data.get('dept_id')
        if class_id:
            from entity.class_ import Class
            cls = self.repo.db.query(Class).filter(Class.class_id == class_id).first()
            if not cls:
                raise ValueError('所选班级不存在')
            if dept_id and cls.major.dept_id != dept_id:
                raise ValueError('所选班级不属于所选学院')
            # 将 dept_id 设置为班级所属专业的学院，确保数据一致性
            filtered_data['dept_id'] = cls.major.dept_id
        
        student = self.repo.get_by_id(student_id)
        if not student:
            return None
        for key, value in filtered_data.items():
            if value is not None and value != '' and hasattr(student, key):
                setattr(student, key, value)
        self.repo.db.commit()
        return student

    def delete(self, student_id: str):
        """删除学生"""
        from entity.enrollment import Enrollment
        from entity.enroll_log import EnrollLog
        from entity.dorm_assignment import DormAssignment
        from entity.reward_punishment import RewardPunishment
        from entity.payment import Payment

        student = self.repo.get_by_id(student_id)
        if not student:
            return False

        # 删除关联记录，避免违反外键约束
        self.repo.db.query(Enrollment).filter(Enrollment.student_id == student_id).delete(synchronize_session=False)
        self.repo.db.query(EnrollLog).filter(EnrollLog.student_id == student_id).delete(synchronize_session=False)
        self.repo.db.query(DormAssignment).filter(DormAssignment.student_id == student_id).delete(synchronize_session=False)
        self.repo.db.query(RewardPunishment).filter(RewardPunishment.student_id == student_id).delete(synchronize_session=False)
        self.repo.db.query(Payment).filter(Payment.student_id == student_id).delete(synchronize_session=False)

        self.repo.delete(student)
        return True

    def get_gpa(self, student_id):
        """计算学生 GPA"""
        from entity.enrollment import Enrollment
        from entity.teaching import Teaching
        from entity.course import Course

        enrollments = self.repo.db.query(Enrollment).join(
            Teaching, Enrollment.teaching_id == Teaching.teaching_id
        ).join(
            Course, Teaching.course_id == Course.course_id
        ).filter(
            Enrollment.student_id == student_id,
            Enrollment.score.isnot(None)
        ).all()

        total_credits = 0
        weighted_gp = 0
        for e in enrollments:
            credit = float(e.teaching.course.credits or 0) if e.teaching and e.teaching.course else 0
            gp = float(e.grade_point or 0)
            total_credits += credit
            weighted_gp += credit * gp

        gpa = round(weighted_gp / total_credits, 2) if total_credits > 0 else 0
        return {'gpa': gpa, 'total_credits': total_credits}

    def get_my_dorm(self, student_id):
        """获取学生的宿舍分配信息"""
        from entity.dorm_assignment import DormAssignment
        from entity.dorm_room import DormRoom

        assignments = self.repo.db.query(DormAssignment).join(
            DormRoom, DormAssignment.room_id == DormRoom.room_id
        ).filter(
            DormAssignment.student_id == student_id
        ).order_by(DormAssignment.check_in_date.desc()).all()

        data = []
        for a in assignments:
            data.append({
                'building': a.room.building if a.room else '',
                'room_number': a.room.room_number if a.room else '',
                'bed_number': a.bed_number or '',
                'check_in_date': str(a.check_in_date) if a.check_in_date else '',
                'check_out_date': str(a.check_out_date) if a.check_out_date else '',
                'status': a.status or '',
            })
        return data
