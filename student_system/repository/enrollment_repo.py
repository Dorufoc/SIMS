from repository.base import BaseRepo
from entity.enrollment import Enrollment


class EnrollmentRepo(BaseRepo):
    model = Enrollment

    field_map = {
        'enroll_id': 'enroll_id',
        'student_id': 'student_id',
        'teaching_id': 'teaching_id',
        'score': 'score',
        'status': 'status',
    }
