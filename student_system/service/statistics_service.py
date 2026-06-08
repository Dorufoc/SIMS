"""统计服务"""
from sqlalchemy import func
from repository.student_repo import StudentRepo
from entity.student import Student
from entity.class_ import Class
from entity.major import Major
from entity.department import Department
from entity.enrollment import Enrollment


class StatisticsService:
    def __init__(self):
        self.repo = StudentRepo()

    def close(self):
        self.repo.close()

    def dashboard(self):
        """仪表盘统计数据"""
        student_count = self.repo.count()
        class_count = self.repo.db.query(Class).count()
        major_count = self.repo.db.query(Major).count()
        dept_count = self.repo.db.query(Department).count()
        active_enrollments = self.repo.db.query(Enrollment).filter(
            Enrollment.status == '正常'
        ).count()

        return {
            'student_count': student_count,
            'class_count': class_count,
            'major_count': major_count,
            'dept_count': dept_count,
            'active_enrollments': active_enrollments,
        }

    def student_by_dept(self):
        """按院系统计学生人数"""
        return self.repo.db.query(
            Department.dept_name,
            func.count(Student.student_id)
        ).join(Student.department).group_by(Department.dept_name).all()

    def student_by_major(self):
        """按专业统计"""
        q = self.repo.db.query(
            Major.major_name,
            func.count(Student.student_id)
        ).select_from(Student).join(Student.class_).join(Class.major).group_by(
            Major.major_name
        ).all()
        return q

    def student_by_class(self):
        """按班级统计"""
        return self.repo.db.query(
            Class.class_name,
            func.count(Student.student_id)
        ).join(Student.class_).group_by(Class.class_name).all()

    def student_by_enrollment_year(self):
        """按年级统计"""
        return self.repo.db.query(
            Student.enrollment_year,
            func.count(Student.student_id)
        ).group_by(Student.enrollment_year).all()

    def gender_distribution(self):
        """性别比例"""
        return self.repo.db.query(
            Student.gender,
            func.count(Student.student_id)
        ).group_by(Student.gender).all()

    def student_status(self):
        """学生状态分布"""
        return self.repo.db.query(
            Student.status,
            func.count(Student.student_id)
        ).group_by(Student.status).all()

    def grade_distribution(self, teaching_id: int = None):
        """成绩分布统计"""
        q = self.repo.db.query(Enrollment.score).filter(Enrollment.score.isnot(None))
        if teaching_id:
            q = q.filter(Enrollment.teaching_id == teaching_id)

        scores = [float(s[0]) for s in q.all()]
        if not scores:
            return {'ranges': [], 'avg': 0, 'total': 0}

        ranges = {
            '90-100': 0, '80-89': 0, '70-79': 0,
            '60-69': 0, '0-59': 0
        }
        for s in scores:
            if s >= 90: ranges['90-100'] += 1
            elif s >= 80: ranges['80-89'] += 1
            elif s >= 70: ranges['70-79'] += 1
            elif s >= 60: ranges['60-69'] += 1
            else: ranges['0-59'] += 1

        return {
            'ranges': ranges,
            'avg': round(sum(scores) / len(scores), 2),
            'total': len(scores),
        }

    def gpa_ranking(self, limit=50):
        """GPA 排名"""
        results = self.repo.db.query(
            Student.student_id, Student.name,
            func.avg(Enrollment.grade_point).label('avg_gpa')
        ).join(Enrollment, Student.student_id == Enrollment.student_id).filter(
            Enrollment.grade_point.isnot(None)
        ).group_by(Student.student_id, Student.name).order_by(
            func.avg(Enrollment.grade_point).desc()
        ).limit(limit).all()

        return [{'student_id': r[0], 'name': r[1], 'gpa': round(float(r[2] or 0), 2)} for r in results]
