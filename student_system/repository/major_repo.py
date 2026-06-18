"""专业 Repository —— 支持跨表关联筛选"""
from typing import List, Dict, Tuple
from repository.base import BaseRepo, escape_like
from entity.major import Major
from entity.department import Department


class MajorRepo(BaseRepo):
    model = Major

    field_map = {
        'major_name': 'major_name',
        'major_id': 'major_id',
        'dept_id': 'dept_id',
        'duration': 'duration',
        'degree_type': 'degree_type',
    }

    def filter_paginate(self, filters: List[Dict], page: int = 1, page_size: int = 10,
                        order_by=None) -> Tuple[List, int]:
        """带筛选条件的分页查询，支持跨表关联字段（如 dept_name）"""
        from sqlalchemy.orm import joinedload

        q = self.db.query(self.model).options(joinedload(Major.department))
        has_dept_join = False

        FIELD_MAP = getattr(self, 'field_map', {})

        for f in filters:
            field = f.get('field', '')
            op = f.get('op', 'eq')
            value = f.get('value', '')

            if not field:
                continue

            # 处理跨表字段 dept_name
            if field == 'dept_name':
                if not has_dept_join:
                    q = q.join(Department, Major.dept_id == Department.dept_id)
                    has_dept_join = True
                column = Department.dept_name
            else:
                if FIELD_MAP and field not in FIELD_MAP:
                    continue
                col_name = FIELD_MAP[field] if FIELD_MAP else field
                column = getattr(self.model, col_name, None)
                if column is None:
                    continue

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
            elif op == 'in_':
                values = [v.strip() for v in value.split(',') if v.strip()]
                if values:
                    q = q.filter(column.in_(values))
            elif op == 'between':
                parts = [v.strip() for v in value.split(',', 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    q = q.filter(column.between(parts[0], parts[1]))

        if order_by is not None:
            q = q.order_by(order_by)

        return self.paginate(page, page_size, q)
