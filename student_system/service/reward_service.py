"""奖惩服务"""
from repository.reward_punishment_repo import RewardPunishmentRepo
from entity.reward_punishment import RewardPunishment


class RewardService:
    def __init__(self):
        self.repo = RewardPunishmentRepo()

    def close(self):
        self.repo.close()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         RewardPunishment.date.desc())

    def get_by_student(self, student_id: str):
        return self.repo.db.query(RewardPunishment).filter(
            RewardPunishment.student_id == student_id
        ).order_by(RewardPunishment.date.desc()).all()

    def create(self, data: dict):
        return self.repo.create(RewardPunishment(**data))

    def update(self, rp_id, data: dict):
        ALLOWED_FIELDS = {'student_id', 'rp_type', 'title', 'level', 'date',
                         'reason', 'issuing_authority', 'remark'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        rp = self.repo.get_by_id(rp_id)
        if not rp:
            return None
        for k, v in filtered_data.items():
            if hasattr(rp, k):
                setattr(rp, k, v)
        self.repo.db.commit()
        return rp

    def delete(self, rp_id):
        return self.repo.delete_by_id(rp_id)
