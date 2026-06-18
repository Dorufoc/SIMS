from repository.base import BaseRepo
from entity.class_ import Class


class ClassRepo(BaseRepo):
    model = Class

    field_map = {
        'class_name': 'class_name',
        'class_id': 'class_id',
        'major_id': 'major_id',
        'enrollment_year': 'enrollment_year',
        'advisor': 'advisor',
    }

    def get_all_with_relations(self):
        from sqlalchemy.orm import joinedload
        from entity.major import Major
        from entity.department import Department
        from entity.teacher import Teacher
        return self.db.query(Class).options(
            joinedload(Class.major).joinedload(Major.department),
            joinedload(Class.teacher)
        ).all()
