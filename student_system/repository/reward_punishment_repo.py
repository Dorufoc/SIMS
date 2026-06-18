from repository.base import BaseRepo
from entity.reward_punishment import RewardPunishment


class RewardPunishmentRepo(BaseRepo):
    model = RewardPunishment

    field_map = {
        'rp_id': 'rp_id',
        'student_id': 'student_id',
        'rp_type': 'rp_type',
        'title': 'title',
        'date': 'date',
    }
