# -*- coding: utf-8 -*-
import os, sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '__pypackages__')
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)
import pytest

class TestMain:

    def test_create_app(self):
        from main import create_app
        app = create_app()
        assert app is not None
        assert app.secret_key is not None
        assert app.config['MAX_CONTENT_LENGTH'] == 10 * 1024 * 1024

    def test_app_routes_registered(self):
        from main import app
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert '/login' in rules
        assert '/register' in rules
        assert '/logout' in rules
        assert '/api/csrf-token' in rules

    def test_app_error_handlers_registered(self):
        from main import app
        spec = app.error_handler_spec.get(None, {})
        assert 404 in spec, '404 错误处理器未注册'
        assert 500 in spec, '500 错误处理器未注册'

    def test_app_security_headers(self):
        from main import app
        app.config['TESTING'] = True
        with app.test_client() as c:
            resp = c.get('/login')
            assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
            assert resp.headers.get('X-Frame-Options') == 'SAMEORIGIN'
