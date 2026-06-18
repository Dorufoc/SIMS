from repository.base import BaseRepo
from entity.dorm_room import DormRoom


class DormRoomRepo(BaseRepo):
    model = DormRoom

    field_map = {
        'room_id': 'room_id',
        'building': 'building',
        'room_number': 'room_number',
        'capacity': 'capacity',
        'occupied': 'occupied',
        'gender_limit': 'gender_limit',
        'phone': 'phone',
    }
