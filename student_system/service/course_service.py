"""课程服务"""
from repository.course_repo import CourseRepo
from entity.course import Course


class CourseService:
    def __init__(self):
        self.repo = CourseRepo()

    def close(self):
        self.repo.close()

    def get_all(self):
        return self.repo.get_all()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Course.course_id)

    def create(self, data: dict):
        return self.repo.create(Course(**data))

    def update(self, course_id, data: dict):
        ALLOWED_FIELDS = {'course_name', 'credits', 'hours', 'type', 'dept_id'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        course = self.repo.get_by_id(course_id)
        if not course:
            return None
        for k, v in filtered_data.items():
            if v is not None and v != '' and hasattr(course, k):
                setattr(course, k, v)
        self.repo.db.commit()
        return course

    def delete(self, course_id):
        return self.repo.delete_by_id(course_id)
