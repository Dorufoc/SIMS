# -*- coding: utf-8 -*-
"""Config 单元测试"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import pytest


class TestConfig:
    """测试 config 模块的配置加载逻辑"""

    def test_secret_key_from_env(self):
        import importlib, config as cfg
        os.environ["SECRET_KEY"] = "my-production-key"
        os.environ["FLASK_ENV"] = "development"
        importlib.reload(cfg)
        assert cfg.SECRET_KEY == "my-production-key"

    def test_database_url_from_env(self):
        import importlib, config as cfg
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
        os.environ["FLASK_ENV"] = "development"
        importlib.reload(cfg)
        assert cfg.DATABASE_URL == "postgresql://test:test@localhost:5432/test_db"

    def test_max_content_length(self):
        import config as cfg
        assert cfg.MAX_CONTENT_LENGTH == 10 * 1024 * 1024
