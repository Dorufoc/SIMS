from repository.base import BaseRepo
from entity.major import Major


class MajorRepo(BaseRepo):
    model = Major

    field_map = {
        'major_name': 'major_name',
        'major_id': 'major_id',
        'dept_id': 'dept_id',
        'duration': 'duration',
    }
