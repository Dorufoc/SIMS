# -*- coding: utf-8 -*-
"""Entity/Base 单元测试"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import pytest


class TestEntityBase:
    """测试 entity/base.py 基础设施"""

    def test_engine_created(self):
        from entity.base import engine
        assert engine is not None
        assert engine.url is not None

    def test_base_metadata_has_tables(self):
        from entity.base import Base
        import entity  # noqa: F401
        assert len(Base.metadata.tables) >= 15
        assert "students" in Base.metadata.tables
        assert "users" in Base.metadata.tables
        assert "departments" in Base.metadata.tables

    def test_get_db_yields_session(self):
        from entity.base import get_db
        gen = get_db()
        db = next(gen)
        assert db is not None
        try:
            next(gen)
        except StopIteration:
            pass
        db.close()

    def test_escape_like(self):
        from repository.base import escape_like
        assert escape_like("hello") == "hello"
        assert escape_like("%") == "\\%"
        assert escape_like("_") == "\\_"
        assert escape_like("\\") == "\\\\"

    def test_is_postgresql(self):
        from entity.base import _is_postgresql
        assert _is_postgresql() is True

    def test_tables_exist_after_init(self):
        """验证 conftest 初始化后的表结构（不重复 drop_all/create_all）"""
        from entity.base import _is_postgresql, Base
        import entity  # noqa: F401
        assert _is_postgresql() is True
        assert len(Base.metadata.tables) >= 15
        assert "students" in Base.metadata.tables
        assert "users" in Base.metadata.tables
        assert "departments" in Base.metadata.tables

    def test_get_db_generator_lifecycle(self):
        """测试 get_db generator 正常 yield 和 close"""
        from entity.base import get_db
        gen = get_db()
        db = next(gen)
        assert db is not None
        # generator should stop iteration after yield
        db.close()
        with pytest.raises(StopIteration):
            next(gen)
