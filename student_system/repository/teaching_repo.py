from repository.base import BaseRepo
from entity.teaching import Teaching


class TeachingRepo(BaseRepo):
    model = Teaching

    field_map = {
        'teaching_id': 'teaching_id',
        'course_id': 'course_id',
        'teacher_id': 'teacher_id',
        'semester_id': 'semester_id',
        'classroom': 'classroom',
        'schedule': 'schedule',
        'capacity': 'capacity',
    }
