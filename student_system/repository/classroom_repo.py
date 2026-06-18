from repository.base import BaseRepo
from entity.classroom import Classroom


class ClassroomRepo(BaseRepo):
    model = Classroom

    field_map = {
        'classroom_id': 'classroom_id',
        'classroom_name': 'classroom_name',
        'building': 'building',
        'floor': 'floor',
        'capacity': 'capacity',
        'type': 'type',
    }
