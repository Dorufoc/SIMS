"""院系服务"""
from repository.department_repo import DepartmentRepo
from entity.department import Department


class DepartmentService:
    def __init__(self):
        self.repo = DepartmentRepo()

    def close(self):
        self.repo.close()

    def get_all(self):
        """获取全部院系"""
        return self.repo.get_all()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Department.dept_name)

    def create(self, data: dict):
        dept = Department(**data)
        return self.repo.create(dept)

    def update(self, dept_id, data: dict):
        ALLOWED_FIELDS = {'dept_name', 'dean', 'phone'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        dept = self.repo.get_by_id(dept_id)
        if not dept:
            return None
        for k, v in filtered_data.items():
            if v is not None and v != '' and hasattr(dept, k):
                setattr(dept, k, v)
        self.repo.db.commit()
        return dept

    def delete(self, dept_id):
        return self.repo.delete_by_id(dept_id)
