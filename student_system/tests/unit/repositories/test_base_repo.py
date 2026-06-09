# -*- coding: utf-8 -*-
"""Repository 层单元测试 - BaseRepo + escape_like"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)
import pytest
from entity.base import Base, engine
from repository.base import BaseRepo, escape_like
from entity.department import Department


class TestEscapeLike:
    """测试 escape_like 工具函数"""

    def test_escape_percent(self):
        result = escape_like("test%value")
        assert "\\%" in result
        assert result == "test\\%value"

    def test_escape_underscore(self):
        result = escape_like("test_value")
        assert "\\_" in result
        assert result == "test\\_value"

    def test_escape_backslash(self):
        result = escape_like("test\\value")
        assert "\\\\" in result

    def test_escape_plain(self):
        assert escape_like("hello") == "hello"
        assert escape_like("") == ""


class TestBaseRepoFilterPaginate:
    """测试 filter_paginate 所有操作符"""

    @pytest.fixture
    def repo(self, reset_tables):
        Base.metadata.create_all(bind=engine)
        r = BaseRepo()
        r.model = Department
        r.field_map = {}
        # 创建测试数据
        for i, name in enumerate(["计算机学院", "数学学院", "外国语学院", "物理学院", "化学学院"]):
            d = Department(dept_name=name, dean=f"dean_{i}", phone=f"010-{10000+i}")
            r.db.add(d)
        r.db.commit()
        yield r
        r.close()

    def test_eq(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_name", "op": "eq", "value": "计算机学院"}])
        assert total == 1
        assert items[0].dept_name == "计算机学院"

    def test_neq(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_name", "op": "neq", "value": "计算机学院"}])
        assert total == 4

    def test_contains(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_name", "op": "contains", "value": "学院"}])
        assert total == 5

    def test_startswith(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_name", "op": "startswith", "value": "计算"}])
        assert total == 1

    def test_endswith(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_name", "op": "endswith", "value": "学院"}])
        assert total == 5

    def test_gt(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_id", "op": "gt", "value": 3}])
        assert total == 2

    def test_gte(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_id", "op": "gte", "value": 3}])
        assert total == 3

    def test_lt(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_id", "op": "lt", "value": 3}])
        assert total == 2

    def test_lte(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_id", "op": "lte", "value": 3}])
        assert total == 3

    def test_in(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_name", "op": "in_", "value": "计算机学院,数学学院"}])
        assert total == 2

    def test_between(self, repo):
        items, total = repo.filter_paginate([{"field": "dept_id", "op": "between", "value": "2,4"}])
        assert total == 3

    def test_combined_filters(self, repo):
        items, total = repo.filter_paginate([
            {"field": "dept_id", "op": "gte", "value": 2},
            {"field": "dept_id", "op": "lte", "value": 4},
        ])
        assert total == 3

    def test_pagination(self, repo):
        items, total = repo.filter_paginate([], page=1, page_size=2)
        assert len(items) == 2
        assert total == 5

    def test_order_by(self, repo):
        repo.model = Department
        from sqlalchemy import asc
        items, total = repo.filter_paginate([], page=1, page_size=10, order_by=Department.dept_id.desc())
        assert items[0].dept_id > items[-1].dept_id

    def test_empty_field_skipped(self, repo):
        items, total = repo.filter_paginate([{"field": "", "op": "eq", "value": "test"}])
        assert total == 5

    def test_unknown_field_skipped(self, repo):
        items, total = repo.filter_paginate([{"field": "nonexistent", "op": "eq", "value": "test"}])
        assert total == 5

    def test_commit_and_close(self, reset_tables):
        Base.metadata.create_all(bind=engine)
        repo = BaseRepo()
        repo.model = Department
        d = Department(dept_name="测试学院", dean="测试院长")
        repo.create(d)
        assert repo.delete_by_id(1) is True
        assert repo.delete_by_id(999) is False
        repo.close()

    def test_rollback(self, reset_tables):
        Base.metadata.create_all(bind=engine)
        repo = BaseRepo()
        repo.model = Department
        repo.rollback()
        repo.close()
