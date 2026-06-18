# -*- coding: utf-8 -*-
"""API 集成测试 — 综合查询 (comprehensive query)"""
import json


class TestQueryAPI:

    def test_query_page(self, client):
        resp = client.get("/query")
        # 未登录会重定向到登录页
        assert resp.status_code in (200, 302)

    def test_query_page_authenticated(self, auth_client):
        resp = auth_client.get("/query")
        assert resp.status_code == 200

    def test_comprehensive_tables(self, auth_client):
        resp = auth_client.get("/api/query/comprehensive/tables")
        data = json.loads(resp.data)
        assert data["ok"] is True
        assert "data" in data

    def test_comprehensive_fields(self, auth_client):
        resp = auth_client.get("/api/query/comprehensive/table/students/fields")
        data = json.loads(resp.data)
        assert data["ok"] is True
        assert "data" in data

    def test_comprehensive_fields_invalid_table(self, auth_client):
        resp = auth_client.get("/api/query/comprehensive/table/nonexistent/fields")
        assert resp.status_code == 404

    def test_comprehensive_relations(self, auth_client):
        resp = auth_client.get("/api/query/comprehensive/table/students/relations")
        data = json.loads(resp.data)
        assert data["ok"] is True
        assert "data" in data

    def test_comprehensive_execute(self, auth_client, populated_db):
        resp = auth_client.post("/api/query/comprehensive/execute", json={
            "main_table": "students",
            "joins": [],
            "filters": [],
            "page": 1
        })
        data = json.loads(resp.data)
        assert data["ok"] is True
        assert "data" in data

    def test_comprehensive_execute_invalid_table(self, auth_client):
        resp = auth_client.post("/api/query/comprehensive/execute", json={
            "main_table": "nonexistent"
        })
        assert resp.status_code == 400

    def test_comprehensive_execute_with_filter(self, auth_client, populated_db):
        resp = auth_client.post("/api/query/comprehensive/execute", json={
            "main_table": "students",
            "joins": [],
            "filters": [{"field": "students.student_id", "op": "=", "value": "2024001"}],
            "page": 1
        })
        data = json.loads(resp.data)
        assert data["ok"] is True

    def test_comprehensive_execute_with_join(self, auth_client, populated_db):
        resp = auth_client.post("/api/query/comprehensive/execute", json={
            "main_table": "students",
            "joins": [{"from_column": "class_id", "to_table": "classes", "to_column": "class_id"}],
            "filters": [],
            "page": 1
        })
        data = json.loads(resp.data)
        assert data["ok"] is True
        assert "data" in data
