"""培养计划服务"""
from repository.curriculum_repo import CurriculumRepo
from entity.curriculum import Curriculum


class CurriculumService:
    def __init__(self):
        self.repo = CurriculumRepo()

    def close(self):
        self.repo.close()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Curriculum.plan_id)

    def get_by_student(self, major_id: int, enrollment_year: int):
        """获取学生培养计划"""
        return self.repo.db.query(Curriculum).filter(
            Curriculum.major_id == major_id,
            Curriculum.enrollment_year == enrollment_year
        ).order_by(Curriculum.recommended_term).all()

    def create(self, data: dict):
        return self.repo.create(Curriculum(**data))

    def update(self, plan_id, data: dict):
        ALLOWED_FIELDS = {'major_id', 'enrollment_year', 'course_id', 'course_type',
                         'recommended_term', 'min_grade', 'is_core', 'remark'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        plan = self.repo.get_by_id(plan_id)
        if not plan:
            return None
        for k, v in filtered_data.items():
            if hasattr(plan, k):
                setattr(plan, k, v)
        self.repo.db.commit()
        return plan

    def delete(self, plan_id):
        return self.repo.delete_by_id(plan_id)
