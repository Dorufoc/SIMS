from repository.base import BaseRepo
from entity.dorm_assignment import DormAssignment


class DormAssignmentRepo(BaseRepo):
    model = DormAssignment

    field_map = {
        'assign_id': 'assign_id',
        'student_id': 'student_id',
        'room_id': 'room_id',
        'bed_number': 'bed_number',
        'status': 'status',
    }
