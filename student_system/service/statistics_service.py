"""统计服务"""
from sqlalchemy import func, case as sql_case
from repository.student_repo import StudentRepo
from entity.student import Student
from entity.class_ import Class
from entity.major import Major
from entity.department import Department
from entity.enrollment import Enrollment
from entity.teaching import Teaching
from entity.course import Course


class StatisticsService:
    def __init__(self):
        self.repo = StudentRepo()

    def close(self):
        self.repo.close()

    def dashboard(self):
        """仪表盘统计数据"""
        from entity.teacher import Teacher
        from entity.course import Course

        student_count = self.repo.count()
        class_count = self.repo.db.query(Class).count()
        major_count = self.repo.db.query(Major).count()
        dept_count = self.repo.db.query(Department).count()
        teacher_count = self.repo.db.query(Teacher).count()
        course_count = self.repo.db.query(Course).count()
        active_enrollments = self.repo.db.query(Enrollment).filter(
            Enrollment.status == '正常'
        ).count()

        return {
            'student_count': student_count,
            'class_count': class_count,
            'major_count': major_count,
            'dept_count': dept_count,
            'teacher_count': teacher_count,
            'course_count': course_count,
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
            Class.class_name,
            Major.major_name,
            func.sum(Course.credits).label('total_credits'),
            func.avg(Enrollment.grade_point).label('avg_gpa')
        ).join(Enrollment, Student.student_id == Enrollment.student_id
        ).join(Class, Student.class_id == Class.class_id
        ).join(Major, Class.major_id == Major.major_id
        ).join(Teaching, Enrollment.teaching_id == Teaching.teaching_id
        ).join(Course, Teaching.course_id == Course.course_id
        ).filter(
            Enrollment.grade_point.isnot(None)
        ).group_by(Student.student_id, Student.name, Class.class_name, Major.major_name
        ).order_by(
            func.avg(Enrollment.grade_point).desc()
        ).limit(limit).all()

        return [{
            'rank': idx + 1,
            'student_id': r[0],
            'name': r[1],
            'class_name': r[2] or '',
            'major_name': r[3] or '',
            'total_credits': round(float(r[4] or 0), 1),
            'avg_gpa': round(float(r[5] or 0), 2),
        } for idx, r in enumerate(results)]

    def class_grade_stats(self, semester_id=None):
        """按班级统计平均成绩和绩点"""
        q = self.repo.db.query(
            Class.class_name,
            Major.major_name,
            Department.dept_name,
            func.count(func.distinct(Enrollment.student_id)).label('student_count'),
            func.avg(Enrollment.score).label('avg_score'),
            func.avg(Enrollment.grade_point).label('avg_gpa'),
        ).select_from(Enrollment
        ).join(Student, Enrollment.student_id == Student.student_id
        ).join(Class, Student.class_id == Class.class_id
        ).join(Major, Class.major_id == Major.major_id
        ).join(Department, Major.dept_id == Department.dept_id
        )

        if semester_id:
            q = q.join(Teaching, Enrollment.teaching_id == Teaching.teaching_id
                      ).filter(Teaching.semester_id == semester_id)

        q = q.group_by(Class.class_name, Major.major_name, Department.dept_name
                      ).order_by(Class.class_name)

        results = q.all()
        return [{
            'class_name': r[0],
            'major_name': r[1],
            'dept_name': r[2],
            'student_count': r[3],
            'avg_score': round(float(r[4] or 0), 2) if r[4] else None,
            'avg_gpa': round(float(r[5] or 0), 2) if r[5] else None,
        } for r in results]

    def age_distribution(self, age_ranges):
        """按年龄段统计学生人数
        age_ranges: 年龄边界列表，如 [18, 20, 22]
        返回: [{'range': '≤18', 'count': 10}, {'range': '18-20', 'count': 25}, ...]
        """
        age_expr = func.floor(
            func.extract('YEAR', func.now()) - func.extract('YEAR', Student.birth_date)
        )

        sorted_ranges = sorted(age_ranges)
        # 构建 CASE WHEN 条件：按顺序匹配第一个满足的范围
        when_clauses = []
        when_clauses.append((age_expr <= sorted_ranges[0], f'≤{sorted_ranges[0]}'))
        for i in range(len(sorted_ranges) - 1):
            low = sorted_ranges[i]
            high = sorted_ranges[i + 1]
            when_clauses.append((age_expr <= high, f'{low}-{high}'))
        when_clauses.append((age_expr > sorted_ranges[-1], f'>{sorted_ranges[-1]}'))

        range_case = sql_case(when_clauses, else_='未知')

        results = self.repo.db.query(
            range_case.label('range'),
            func.count(Student.student_id)
        ).filter(
            Student.birth_date.isnot(None)
        ).group_by(
            range_case
        ).all()

        return [{'range': r[0], 'count': r[1]} for r in results]

    def age_stats_by_major(self):
        """按专业统计年龄（平均年龄、最大年龄、最小年龄）"""
        age_expr = func.floor(
            func.extract('YEAR', func.now()) - func.extract('YEAR', Student.birth_date)
        )

        results = self.repo.db.query(
            Major.major_name,
            func.avg(age_expr).label('avg_age'),
            func.max(age_expr).label('max_age'),
            func.min(age_expr).label('min_age')
        ).select_from(Student
        ).join(Student.class_
        ).join(Class.major
        ).filter(
            Student.birth_date.isnot(None)
        ).group_by(
            Major.major_name
        ).all()

        return [{
            'major': r[0],
            'avg_age': round(float(r[1]), 1) if r[1] else 0,
            'max_age': int(r[2]) if r[2] else 0,
            'min_age': int(r[3]) if r[3] else 0,
        } for r in results]

    def grade_avg_age(self):
        """按入学年级统计平均年龄"""
        age_expr = func.floor(
            func.extract('YEAR', func.now()) - func.extract('YEAR', Student.birth_date)
        )

        results = self.repo.db.query(
            Student.enrollment_year,
            func.avg(age_expr).label('avg_age')
        ).filter(
            Student.birth_date.isnot(None)
        ).group_by(
            Student.enrollment_year
        ).order_by(
            Student.enrollment_year
        ).all()

        return [{'grade': str(r[0]), 'avg_age': round(float(r[1]), 1)} for r in results]

    def age_range_stats(self, min_age, max_age):
        """统计特定年龄范围内的学生人数"""
        age_expr = func.floor(
            func.extract('YEAR', func.now()) - func.extract('YEAR', Student.birth_date)
        )

        count = self.repo.db.query(
            func.count(Student.student_id)
        ).filter(
            Student.birth_date.isnot(None),
            age_expr >= min_age,
            age_expr <= max_age
        ).scalar()

        return {'count': count or 0}

    def student_count_with_birth_date(self):
        """统计有出生日期记录的学生人数"""
        return self.repo.db.query(
            func.count(Student.student_id)
        ).filter(
            Student.birth_date.isnot(None)
        ).scalar() or 0
