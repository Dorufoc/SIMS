from repository.base import BaseRepo
from entity.teacher import Teacher


class TeacherRepo(BaseRepo):
    model = Teacher

    field_map = {
        'teacher_id': 'teacher_id',
        'name': 'name',
        'gender': 'gender',
        'title': 'title',
        'dept_id': 'dept_id',
        'phone': 'phone',
        'email': 'email',
    }
