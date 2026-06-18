from typing import List, Dict, Tuple
from repository.base import BaseRepo, escape_like
from entity.student import Student
from entity.class_ import Class
from entity.major import Major
from entity.department import Department
from sqlalchemy import func
from sqlalchemy.orm import joinedload


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

    def filter_paginate(self, filters: List[Dict], page: int = 1, page_size: int = 10,
                        order_by=None) -> Tuple[List, int]:
        """带筛选条件的分页查询（支持关联字段：class_name, major_name, dept_name）"""
        q = self.db.query(Student).options(
            joinedload(Student.class_).joinedload(Class.major).joinedload(Major.department)
        )

        has_class_join = False
        has_major_join = False
        has_dept_join = False

        for f in filters:
            field = f.get('field', '')
            op = f.get('op', 'eq')
            value = f.get('value', '')

            if not field:
                continue

            # 处理关联字段筛选
            if field == 'class_name':
                if not has_class_join:
                    q = q.join(Class, Student.class_id == Class.class_id)
                    has_class_join = True
                column = Class.class_name
            elif field == 'major_name':
                if not has_class_join:
                    q = q.join(Class, Student.class_id == Class.class_id)
                    has_class_join = True
                if not has_major_join:
                    q = q.join(Major, Class.major_id == Major.major_id)
                    has_major_join = True
                column = Major.major_name
            elif field == 'dept_name':
                if not has_class_join:
                    q = q.join(Class, Student.class_id == Class.class_id)
                    has_class_join = True
                if not has_major_join:
                    q = q.join(Major, Class.major_id == Major.major_id)
                    has_major_join = True
                if not has_dept_join:
                    q = q.join(Department, Major.dept_id == Department.dept_id)
                    has_dept_join = True
                column = Department.dept_name
            else:
                # 直接字段（Student 表的列）
                col_name = self.field_map.get(field)
                if col_name is None:
                    continue
                column = getattr(Student, col_name, None)
                if column is None:
                    continue

            # 应用操作符
            if op == 'eq':
                q = q.filter(column == value)
            elif op == 'neq':
                q = q.filter(column != value)
            elif op == 'contains':
                q = q.filter(column.like(f'%{escape_like(value)}%', escape='\\'))
            elif op == 'startswith':
                q = q.filter(column.like(f'{escape_like(value)}%', escape='\\'))
            elif op == 'endswith':
                q = q.filter(column.like(f'%{escape_like(value)}', escape='\\'))
            elif op == 'gt':
                q = q.filter(column > value)
            elif op == 'gte':
                q = q.filter(column >= value)
            elif op == 'lt':
                q = q.filter(column < value)
            elif op == 'lte':
                q = q.filter(column <= value)
            elif op == 'in':
                values = [v.strip() for v in value.split(',') if v.strip()]
                if values:
                    q = q.filter(column.in_(values))
            elif op == 'between':
                parts = [v.strip() for v in value.split(',', 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    q = q.filter(column.between(parts[0], parts[1]))

        if order_by is not None:
            q = q.order_by(order_by)
        else:
            q = q.order_by(Student.student_id)

        return self.paginate(page, page_size, q)
