from repository.base import BaseRepo
from entity.semester import Semester


class SemesterRepo(BaseRepo):
    model = Semester

    field_map = {
        'semester_id': 'semester_id',
        'academic_year': 'academic_year',
        'semester_name': 'semester_name',
    }

    def find_current(self):
        return self.find_by(is_current=True)
