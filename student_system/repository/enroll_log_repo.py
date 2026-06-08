from repository.base import BaseRepo
from entity.enroll_log import EnrollLog


class EnrollLogRepo(BaseRepo):
    model = EnrollLog

    field_map = {
        'log_id': 'log_id',
        'student_id': 'student_id',
        'teaching_id': 'teaching_id',
        'operation_type': 'operation_type',
    }
