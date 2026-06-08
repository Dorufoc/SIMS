from repository.base import BaseRepo
from entity.class_ import Class


class ClassRepo(BaseRepo):
    model = Class

    field_map = {
        'class_name': 'class_name',
        'class_id': 'class_id',
        'major_id': 'major_id',
        'enrollment_year': 'enrollment_year',
        'advisor': 'advisor',
    }
