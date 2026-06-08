"""学期服务"""
from repository.semester_repo import SemesterRepo
from entity.semester import Semester


class SemesterService:
    def __init__(self):
        self.repo = SemesterRepo()

    def close(self):
        self.repo.close()

    def get_all(self):
        return self.repo.db.query(Semester).order_by(
            Semester.academic_year.desc(), Semester.semester_name
        ).all()

    def get_list(self, page=1, page_size=10, filters=None):
        return self.repo.filter_paginate(filters or [], page, page_size,
                                         Semester.academic_year.desc())

    def create(self, data: dict):
        return self.repo.create(Semester(**data))

    def update(self, semester_id, data: dict):
        ALLOWED_FIELDS = {'academic_year', 'semester_name', 'start_date', 'end_date', 'is_current'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        sem = self.repo.get_by_id(semester_id)
        if not sem:
            return None
        for k, v in filtered_data.items():
            if hasattr(sem, k):
                setattr(sem, k, v)
        self.repo.db.commit()
        return sem

    def delete(self, semester_id):
        return self.repo.delete_by_id(semester_id)

    def set_current(self, semester_id):
        """设置当前学期"""
        # 先取消所有当前标记
        all_semesters = self.repo.get_all()
        for s in all_semesters:
            s.is_current = False
        # 设置新的当前学期
        sem = self.repo.get_by_id(semester_id)
        if sem:
            sem.is_current = True
            self.repo.db.commit()
            return True
        return False

    def get_current(self):
        """获取当前学期"""
        return self.repo.find_current()
