from repository.base import BaseRepo
from entity.curriculum import Curriculum


class CurriculumRepo(BaseRepo):
    model = Curriculum

    field_map = {
        'plan_id': 'plan_id',
        'major_id': 'major_id',
        'enrollment_year': 'enrollment_year',
        'course_id': 'course_id',
        'course_type': 'course_type',
    }
