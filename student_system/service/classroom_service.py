"""教室服务"""
from repository.classroom_repo import ClassroomRepo
from entity.classroom import Classroom


class ClassroomService:
    def __init__(self):
        self.repo = ClassroomRepo()

    def close(self):
        self.repo.close()

    def get_all(self):
        return self.repo.get_all()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Classroom.classroom_id.desc())

    def create(self, data: dict):
        return self.repo.create(Classroom(**data))

    def update(self, classroom_id, data: dict):
        ALLOWED_FIELDS = {'classroom_name', 'building', 'floor', 'capacity', 'type'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        classroom = self.repo.get_by_id(classroom_id)
        if not classroom:
            return None
        for k, v in filtered_data.items():
            if v is not None and v != '' and hasattr(classroom, k):
                setattr(classroom, k, v)
        self.repo.db.commit()
        return classroom

    def delete(self, classroom_id):
        return self.repo.delete_by_id(classroom_id)
