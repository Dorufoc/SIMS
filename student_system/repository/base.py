"""基础 Repository 类，提供通用 CRUD 和分页功能"""
from typing import Optional, List, Tuple, Type, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import cast, String, Integer, Date, DateTime
from entity.base import SessionLocal


def escape_like(value: str) -> str:
    """转义 LIKE 查询中的通配符 % 和 _"""
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


class BaseRepo:
    model: Type[Any] = None  # 子类覆盖

    def __init__(self, session=None):
        self.db: Session = session if session is not None else SessionLocal()
        self._owns_session = session is None  # track if we own this session

    def commit(self):
        if self._owns_session:
            self.db.commit()

    def rollback(self):
        if self._owns_session:
            self.db.rollback()

    def close(self):
        if self._owns_session:
            self.db.close()

    def get_by_id(self, id):
        return self.db.get(self.model, id)

    def get_all(self):
        return self.db.query(self.model).all()

    def find_by(self, **kwargs):
        return self.db.query(self.model).filter_by(**kwargs).first()

    def find_all_by(self, **kwargs):
        return self.db.query(self.model).filter_by(**kwargs).all()

    def create(self, entity, auto_commit: bool = True):
        self.db.add(entity)
        if auto_commit:
            self.db.commit()
            self.db.refresh(entity)
        else:
            self.db.flush()
        return entity

    def update(self, entity, auto_commit: bool = True):
        self.db.merge(entity)
        if auto_commit:
            self.db.commit()
        else:
            self.db.flush()
        return entity

    def delete(self, entity, auto_commit: bool = True):
        self.db.delete(entity)
        if auto_commit:
            self.db.commit()
        else:
            self.db.flush()

    def delete_by_id(self, id):
        entity = self.get_by_id(id)
        if entity:
            self.delete(entity)
            return True
        return False

    def count(self) -> int:
        return self.db.query(self.model).count()

    def paginate(self, page: int = 1, page_size: int = 10, query=None) -> Tuple[List, int]:
        """分页查询
        page <= 0 时返回全部记录，不做分页
        Returns: (items, total)
        """
        q = query if query is not None else self.db.query(self.model)
        total = q.count()
        if page <= 0:
            items = q.all()
        else:
            items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def filter_paginate(self, filters: List[Dict], page: int = 1, page_size: int = 10,
                        order_by=None) -> Tuple[List, int]:
        """带筛选条件的分页查询
        filters: list of dict with keys: field, op, value
        支持的操作符: eq, neq, contains, startswith, endswith, gt, gte, lt, lte, between
        """
        q = self.db.query(self.model)

        FIELD_MAP = getattr(self, 'field_map', {})

        for f in filters:
            field = f.get('field', '')
            op = f.get('op', 'eq')
            value = f.get('value', '')

            if not field:
                continue

            if FIELD_MAP:
                if field not in FIELD_MAP:
                    continue
                col_name = FIELD_MAP[field]
            else:
                col_name = field

            column = getattr(self.model, col_name, None)
            if column is None:
                continue

            # 对整数、日期列使用字符串运算符时自动转型
            if isinstance(column.type, Integer) and op in ('contains', 'startswith', 'endswith'):
                column = cast(column, String)
            if isinstance(column.type, (Date, DateTime)) and op in ('contains', 'startswith', 'endswith'):
                column = cast(column, String)

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
            elif op == 'between':
                parts = [v.strip() for v in value.split(',', 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    q = q.filter(column.between(parts[0], parts[1]))

        if order_by is not None:
            q = q.order_by(order_by)

        return self.paginate(page, page_size, q)
