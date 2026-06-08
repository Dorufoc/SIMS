from repository.base import BaseRepo
from entity.payment import Payment


class PaymentRepo(BaseRepo):
    model = Payment

    field_map = {
        'payment_id': 'payment_id',
        'student_id': 'student_id',
        'fee_type': 'fee_type',
        'academic_year': 'academic_year',
        'status': 'status',
    }
