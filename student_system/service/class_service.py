"""班级服务"""
from repository.class_repo import ClassRepo
from entity.class_ import Class


class ClassService:
    def __init__(self):
        self.repo = ClassRepo()

    def close(self):
        self.repo.close()

    def get_all(self):
        return self.repo.get_all()

    def get_list(self, page=1, page_size=10, filters=None, major_id=None):
        q = self.repo.db.query(Class)
        if major_id:
            q = q.filter(Class.major_id == major_id)
        return self.repo.paginate(page, page_size, q)

    def create(self, data: dict):
        return self.repo.create(Class(**data))

    def update(self, class_id, data: dict):
        ALLOWED_FIELDS = {'class_name', 'major_id', 'enrollment_year', 'advisor'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        cls = self.repo.get_by_id(class_id)
        if not cls:
            return None
        for k, v in filtered_data.items():
            if hasattr(cls, k):
                setattr(cls, k, v)
        self.repo.db.commit()
        return cls

    def delete(self, class_id):
        return self.repo.delete_by_id(class_id)
