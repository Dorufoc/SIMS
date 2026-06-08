"""成绩服务"""
from repository.enrollment_repo import EnrollmentRepo
from entity.enrollment import Enrollment
from entity.grade_scale import GradeScale
from sqlalchemy import func


class GradeService:
    def __init__(self):
        self.repo = EnrollmentRepo()

    def close(self):
        self.repo.close()

    def _calc_grade_point(self, score):
        """根据成绩计算绩点"""
        scales = self.repo.db.query(GradeScale).order_by(
            GradeScale.min_score.desc()
        ).all()
        for s in scales:
            if score is not None and s.min_score is not None and s.max_score is not None and float(score) >= float(s.min_score) and float(score) <= float(s.max_score):
                return float(s.grade_point)
        return 0.0

    def set_score(self, enroll_id: int, score):
        """录入/修改单个成绩"""
        enrollment = self.repo.get_by_id(enroll_id)
        if not enrollment:
            return False, '选课记录不存在'

        try:
            score = float(score)
        except (ValueError, TypeError):
            return False, '成绩格式不正确'

        enrollment.score = score
        enrollment.grade_point = self._calc_grade_point(score)
        self.repo.db.commit()
        return True, '成绩录入成功'

    def batch_score(self, scores_data: list):
        """批量录入成绩
        scores_data: [{'enroll_id': 1, 'score': 85}, ...]
        """
        for item in scores_data:
            enrollment = self.repo.get_by_id(item['enroll_id'])
            if enrollment:
                score = item.get('score')
                try:
                    score = float(score)
                except (ValueError, TypeError):
                    continue
                enrollment.score = score
                enrollment.grade_point = self._calc_grade_point(score)
        self.repo.db.commit()
        return True, f'批量录入完成，共{len(scores_data)}条'

    def get_teaching_students(self, teaching_id: int):
        """获取授课班级的学生成绩列表"""
        return self.repo.db.query(Enrollment).filter(
            Enrollment.teaching_id == teaching_id
        ).all()

    def get_student_scores(self, student_id: str):
        """获取学生成绩单"""
        return self.repo.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.score.isnot(None)
        ).order_by(Enrollment.teaching_id.desc()).all()

    def get_course_score_stats(self, teaching_id: int):
        """获取课程成绩统计"""
        scores = self.repo.db.query(Enrollment.score).filter(
            Enrollment.teaching_id == teaching_id,
            Enrollment.score.isnot(None)
        ).all()
        if not scores:
            return {'avg': 0, 'max': 0, 'min': 0, 'count': 0}
        score_list = [float(s[0]) for s in scores]
        return {
            'avg': round(sum(score_list) / len(score_list), 2),
            'max': max(score_list),
            'min': min(score_list),
            'count': len(score_list),
        }
