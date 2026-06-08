"""选课服务"""
from repository.enrollment_repo import EnrollmentRepo
from entity.enrollment import Enrollment
from entity.teaching import Teaching
from entity.course import Course


class EnrollmentService:
    def __init__(self):
        self.repo = EnrollmentRepo()

    def close(self):
        self.repo.close()

    def get_available_courses(self, student_id: str):
        """获取可选课程列表"""
        # 简单实现：返回所有未被该学生选的课程
        enrolled_ids = self.repo.db.query(Enrollment.teaching_id).filter(
            Enrollment.student_id == student_id,
            Enrollment.status != '退课'
        ).subquery()

        q = self.repo.db.query(Teaching).filter(
            ~Teaching.teaching_id.in_(enrolled_ids)
        ).order_by(Teaching.teaching_id)
        return q.all()

    def enroll(self, student_id: str, teaching_id: int):
        """学生选课"""
        # 检查是否已选
        existing = self.repo.find_by(student_id=student_id, teaching_id=teaching_id)
        if existing:
            if existing.status == '退课':
                existing.status = '正常'
                self.repo.db.commit()
                return True, '重新选课成功'
            return False, '已选该课程'

        # 检查课程容量
        teaching = self.repo.db.query(Teaching).filter(
            Teaching.teaching_id == teaching_id
        ).first()
        if not teaching:
            return False, '课程不存在'
        
        enrolled_count = self.repo.db.query(Enrollment).filter(
            Enrollment.teaching_id == teaching_id,
            Enrollment.status != '退课'
        ).count()
        if teaching.capacity and enrolled_count >= teaching.capacity:
            return False, '课程容量已满'

        # 检查时间冲突
        if teaching.schedule:
            enrolled_teachings = self.repo.db.query(Enrollment.teaching_id).filter(
                Enrollment.student_id == student_id,
                Enrollment.status != '退课'
            ).all()
            enrolled_t_ids = [e[0] for e in enrolled_teachings]
            if enrolled_t_ids:
                conflicting = self.repo.db.query(Teaching).filter(
                    Teaching.teaching_id.in_(enrolled_t_ids),
                    Teaching.schedule == teaching.schedule
                ).first()
                if conflicting:
                    return False, f'与课程时间 {teaching.schedule} 冲突'

        enrollment = Enrollment(
            student_id=student_id,
            teaching_id=teaching_id,
            status='正常'
        )
        self.repo.create(enrollment)
        return True, '选课成功'

    def drop(self, enroll_id: int):
        """退课"""
        enrollment = self.repo.get_by_id(enroll_id)
        if not enrollment:
            return False, '选课记录不存在'
        enrollment.status = '退课'
        self.repo.db.commit()
        return True, '退课成功'

    def get_student_enrollments(self, student_id: str):
        """获取学生选课记录"""
        return self.repo.find_all_by(student_id=student_id)
