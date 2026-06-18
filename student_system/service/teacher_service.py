"""教师服务"""
from repository.teacher_repo import TeacherRepo
from entity.teacher import Teacher


class TeacherService:
    def __init__(self):
        self.repo = TeacherRepo()

    def close(self):
        self.repo.close()

    def get_all(self):
        return self.repo.get_all()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Teacher.teacher_id)

    def get_by_id(self, teacher_id):
        return self.repo.get_by_id(teacher_id)

    def create(self, data: dict):
        return self.repo.create(Teacher(**data))

    def update(self, teacher_id, data: dict):
        ALLOWED_FIELDS = {'name', 'gender', 'title', 'dept_id', 'phone', 'email'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        teacher = self.repo.get_by_id(teacher_id)
        if not teacher:
            return None
        for k, v in filtered_data.items():
            if v is not None and v != '' and hasattr(teacher, k):
                setattr(teacher, k, v)
        self.repo.db.commit()
        return teacher

    def delete(self, teacher_id):
        return self.repo.delete_by_id(teacher_id)
