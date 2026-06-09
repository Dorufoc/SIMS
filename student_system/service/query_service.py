"""高级查询服务"""
from repository.student_repo import StudentRepo
from repository.base import escape_like
from entity.student import Student
from entity.class_ import Class
from entity.major import Major
from entity.department import Department
from sqlalchemy import or_, and_


# 允许的字段名白名单（防 SQL 注入）
ALLOWED_FIELDS = {
    'student_id', 'name', 'gender', 'birth_date', 'enrollment_year',
    'status', 'phone', 'email', 'class_name', 'major_name', 'dept_name'
}

ALLOWED_OPERATORS = {'=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN', 'NOT_IN', 'BETWEEN', 'IS_NULL', 'IS_NOT_NULL'}


class QueryService:
    def __init__(self):
        self.repo = StudentRepo()

    def close(self):
        self.repo.close()

    def dynamic_query(self, conditions: list):
        """动态条件查询"""
        q = self.repo.db.query(Student).join(Student.class_).join(
            Class.major
        ).join(Major.department)

        condition_groups = []
        for i, cond in enumerate(conditions):
            field = cond.get('field', '')
            operator = cond.get('operator', '')
            value = cond.get('value', '')
            value_to = cond.get('value_to', '')
            logic = cond.get('logic', 'AND')
            not_flag = cond.get('not', False)

            if field not in ALLOWED_FIELDS:
                continue
            if operator not in ALLOWED_OPERATORS:
                continue

            # 构建条件
            if field in ('class_name', 'major_name', 'dept_name'):
                if field == 'class_name':
                    col = Class.class_name
                elif field == 'major_name':
                    col = Major.major_name
                else:
                    col = Department.dept_name
            else:
                col = getattr(Student, field, None)

            if col is None:
                continue

            if operator == 'LIKE':
                condition = col.like(f'%{escape_like(value)}%', escape='\\')
            elif operator == '=':
                condition = col == value
            elif operator == '!=':
                condition = col != value
            elif operator == '>':
                condition = col > value
            elif operator == '<':
                condition = col < value
            elif operator == '>=':
                condition = col >= value
            elif operator == '<=':
                condition = col <= value
            elif operator == 'IN':
                values = [v.strip() for v in value.split(',') if v.strip()]
                condition = col.in_(values)
            elif operator == 'NOT_IN':
                values = [v.strip() for v in value.split(',') if v.strip()]
                condition = ~col.in_(values)
            elif operator == 'BETWEEN':
                condition = col.between(value, value_to)
            elif operator == 'IS_NULL':
                condition = col.is_(None)
            elif operator == 'IS_NOT_NULL':
                condition = col.isnot(None)
            else:
                continue

            if not_flag:
                condition = ~condition

            condition_groups.append((condition, logic))

        # 根据 logic 组合条件
        if condition_groups:
            final_condition = condition_groups[0][0]
            for cond, logic in condition_groups[1:]:
                if logic == 'OR':
                    final_condition = or_(final_condition, cond)
                else:
                    final_condition = and_(final_condition, cond)
            q = q.filter(final_condition)

        return q.all()

    def sort_query(self, sort_fields: list, page: int = 1, page_size: int = 10):
        """多字段排序分页查询"""
        valid_sort = []
        for sf in sort_fields:
            field = sf.get('field', '')
            order = sf.get('order', 'asc')
            if field in ALLOWED_FIELDS and order in ('asc', 'desc'):
                if field in ('class_name', 'major_name', 'dept_name'):
                    if field == 'class_name':
                        col = Class.class_name
                    elif field == 'major_name':
                        col = Major.major_name
                    else:
                        col = Department.dept_name
                else:
                    col = getattr(Student, field, None)
                if col is not None:
                    valid_sort.append(col.asc() if order == 'asc' else col.desc())

        q = self.repo.db.query(Student).join(Student.class_).join(
            Class.major
        ).join(Major.department)

        if valid_sort:
            q = q.order_by(*valid_sort)
        else:
            q = q.order_by(Student.student_id)

        return self.repo.paginate(page, page_size, q)
