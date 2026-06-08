"""授课服务"""
from repository.teaching_repo import TeachingRepo
from entity.teaching import Teaching


class TeachingService:
    def __init__(self):
        self.repo = TeachingRepo()

    def close(self):
        self.repo.close()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Teaching.teaching_id.desc())

    def get_by_teacher(self, teacher_id: str):
        """获取教师的授课列表"""
        q = self.repo.db.query(Teaching).filter(
            Teaching.teacher_id == teacher_id
        ).order_by(Teaching.semester_id.desc())
        return q.all()

    def create(self, data: dict):
        return self.repo.create(Teaching(**data))

    def update(self, teaching_id, data: dict):
        ALLOWED_FIELDS = {'course_id', 'teacher_id', 'semester_id', 'classroom', 'schedule', 'capacity'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        t = self.repo.get_by_id(teaching_id)
        if not t:
            return None
        for k, v in filtered_data.items():
            if hasattr(t, k):
                setattr(t, k, v)
        self.repo.db.commit()
        return t

    def delete(self, teaching_id):
        return self.repo.delete_by_id(teaching_id)
