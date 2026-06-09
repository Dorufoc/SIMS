# -*- coding: utf-8 -*-
"""API 集成测试 — 查询"""
import json
import pytest

class TestQueryAPI:

    def test_query_page(self, client):
        resp = client.get("/query")
        # redirects to login if no session
        assert resp.status_code in (200, 302)

    def test_filter_query_empty(self, auth_client):
        resp = auth_client.post("/query/filter", json={})
        data = json.loads(resp.data)
        assert "ok" in data or "data" in data

    def test_filter_query_with_data(self, auth_client, populated_db):
        resp = auth_client.post("/query/filter", json={
            "filters": [{"field": "student_name", "operator": "eq", "value": "张三"}],
            "page": 1
        })
        data = json.loads(resp.data)
        assert "data" in data

    def test_sort_query(self, auth_client):
        resp = auth_client.post("/query/sort", json={"sort_fields": [{"field": "student_id", "order": "asc"}], "page": 1})
        data = json.loads(resp.data)
        assert "page" in data

    def test_sort_query_legacy(self, auth_client):
        resp = auth_client.post("/query/sort", json={"sort_field": "student_id", "sort_order": "asc", "page": 1})
        data = json.loads(resp.data)
        assert "page" in data

    def test_sort_query_empty_fields(self, auth_client):
        resp = auth_client.post("/query/sort", json={"page": 1})
        data = json.loads(resp.data)
        assert "page" in data

    def test_query_build_empty(self, auth_client):
        resp = auth_client.post("/query/build", json={"conditions": []})
        data = json.loads(resp.data)
        assert "data" in data or "columns" in data

    def test_query_scene_by_student_no(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_student_no", "params": {"val1": "2024001"}})
        data = json.loads(resp.data)
        assert "desc" in data
        assert "场景查询" in data["desc"]

    def test_query_scene_by_name(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_student_name", "params": {"val1": "张三"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_by_major(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_major", "params": {"val1": "计算机"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_by_dept(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_dept", "params": {"val1": "计算机"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_by_grade(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_grade", "params": {"val1": "2024"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_by_gender(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_gender", "params": {"val1": "男"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_by_class(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_class", "params": {"val1": "计科"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_by_name_like(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_name_like", "params": {"val1": "张"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_not_dept(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "not_dept", "params": {"val1": "计算机学院"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_not_major(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_not_major", "params": {"val1": "计算机"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_age_range(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_age_range", "params": {"val1": "2000-01-01", "val2": "2005-01-01"}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_scene_no_params(self, auth_client):
        resp = auth_client.post("/query/scene", json={"scene": "by_student_no", "params": {}})
        data = json.loads(resp.data)
        assert "desc" in data

    def test_query_keyword_detail(self, auth_client):
        resp = auth_client.get("/query/keyword?keyword=SELECT")
        data = json.loads(resp.data)
        assert data["keyword"] == "SELECT"
        assert "description" in data

    def test_query_keyword_detail_not_found(self, auth_client):
        resp = auth_client.get("/query/keyword?keyword=UNKNOWN")
        data = json.loads(resp.data)
        assert "暂未收录" in data.get("description", "")

    @pytest.mark.xfail(reason='接口 /query/keyword/execute 不存在，实际为 /query/keyword (GET)')
    def test_query_keyword_execute(self, auth_client):
        resp = auth_client.post("/query/keyword/execute", json={"keyword": "SELECT"})
        data = json.loads(resp.data)
        assert data["code"] is True

    @pytest.mark.xfail(reason='接口 /query/keyword/execute 不存在')
    def test_query_keyword_execute_dangerous_non_admin(self, student_client):
        resp = student_client.post("/query/keyword/execute", json={"keyword": "DROP_TABLE"})
        data = json.loads(resp.data)
        assert data["code"] is False

    @pytest.mark.xfail(reason='接口 /query/keyword/execute 不存在')
    def test_query_keyword_execute_dangerous_admin(self, auth_client):
        resp = auth_client.post("/query/keyword/execute", json={"keyword": "DROP_TABLE"})
        data = json.loads(resp.data)
        assert data["code"] is True

    def test_query_stat(self, auth_client):
        resp = auth_client.post("/query/stat", json={})
        data = json.loads(resp.data)
        assert "data" in data or "columns" in data

    def test_query_stat_with_params(self, auth_client):
        resp = auth_client.post("/query/stat-with-params", json={})
        data = json.loads(resp.data)
        assert "data" in data or "columns" in data
