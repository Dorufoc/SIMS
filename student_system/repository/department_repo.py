from repository.base import BaseRepo
from entity.department import Department


class DepartmentRepo(BaseRepo):
    model = Department

    field_map = {
        'dept_name': 'dept_name',
        'dean': 'dean',
        'phone': 'phone',
        'dept_id': 'dept_id',
    }

    def find_by_name(self, name: str):
        return self.find_by(dept_name=name)
