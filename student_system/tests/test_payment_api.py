# -*- coding: utf-8 -*-
"""API 集成测试 — 缴费"""
import json

class TestPaymentAPI:
    def test_create(self, auth_client):
        c = auth_client
        c.post('/add', data={"student_id":"P001","name":"测试缴费","enrollment_year":"2024"})
        resp = c.post('/api/payments', json={"student_id":"P001","fee_type":"学费","academic_year":"2024-2025","semester":"第一学期","amount_due":5000})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_pay(self, auth_client):
        c = auth_client
        c.post('/add', data={"student_id":"P001","name":"测试缴费","enrollment_year":"2024"})
        c.post('/api/payments', json={"student_id":"P001","fee_type":"学费","academic_year":"2024-2025","semester":"第一学期","amount_due":5000})
        resp = c.post('/api/payments/1/pay', json={"amount":5000,"method":"微信"})
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_overdue(self, auth_client):
        resp = auth_client.get('/api/payments/overdue')
        data = json.loads(resp.data)
        assert data["code"] == 0

    def test_get_stats(self, auth_client):
        resp = auth_client.get('/api/payments/stats')
        data = json.loads(resp.data)
        assert data["code"] == 0
