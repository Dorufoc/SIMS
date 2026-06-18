"""专业服务"""
from repository.major_repo import MajorRepo
from entity.major import Major


class MajorService:
    def __init__(self):
        self.repo = MajorRepo()

    def close(self):
        self.repo.close()

    def get_all(self):
        return self.repo.get_all()

    def get_list(self, page=1, page_size=10, filters=None, dept_id=None):
        q = self.repo.db.query(Major)
        if dept_id:
            q = q.filter(Major.dept_id == dept_id)
        return self.repo.paginate(page, page_size, q)

    def create(self, data: dict):
        return self.repo.create(Major(**data))

    def update(self, major_id, data: dict):
        ALLOWED_FIELDS = {'major_name', 'dept_id', 'duration', 'degree_type', 'description'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        major = self.repo.get_by_id(major_id)
        if not major:
            return None
        for k, v in filtered_data.items():
            if v is not None and v != '' and hasattr(major, k):
                setattr(major, k, v)
        self.repo.db.commit()
        return major

    def delete(self, major_id):
        return self.repo.delete_by_id(major_id)
