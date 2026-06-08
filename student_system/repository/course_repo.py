from repository.base import BaseRepo
from entity.course import Course


class CourseRepo(BaseRepo):
    model = Course

    field_map = {
        'course_id': 'course_id',
        'course_name': 'course_name',
        'credits': 'credits',
        'hours': 'hours',
        'type': 'type',
        'dept_id': 'dept_id',
    }
