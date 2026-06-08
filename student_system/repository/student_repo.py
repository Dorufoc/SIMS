from repository.base import BaseRepo, escape_like
from entity.student import Student
from sqlalchemy import func


class StudentRepo(BaseRepo):
    model = Student

    field_map = {
        'student_id': 'student_id',
        'name': 'name',
        'gender': 'gender',
        'enrollment_year': 'enrollment_year',
        'status': 'status',
        'phone': 'phone',
        'email': 'email',
        'class_id': 'class_id',
        'dept_id': 'dept_id',
    }

    def find_by_student_id(self, student_id: str):
        return self.find_by(student_id=student_id)

    def search(self, keyword: str, page: int = 1, page_size: int = 10):
        escaped = escape_like(keyword)
        q = self.db.query(Student).filter(
            (Student.student_id.like(f'%{escaped}%', escape='\\')) |
            (Student.name.like(f'%{escaped}%', escape='\\')) |
            (Student.phone.like(f'%{escaped}%', escape='\\')) |
            (Student.email.like(f'%{escaped}%', escape='\\'))
        )
        return self.paginate(page, page_size, q)
