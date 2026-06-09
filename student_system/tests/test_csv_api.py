# -*- coding: utf-8 -*-
"""API 集成测试 — CSV"""
import json

class TestCSVAPI:
    def test_template(self, auth_client):
        resp = auth_client.get('/csv/template')
        assert resp.status_code in (200, 302)

    def test_export(self, auth_client):
        resp = auth_client.get('/csv/export')
        assert resp.status_code in (200, 302)
