# -*- coding: utf-8 -*-
"""API 集成测试 — 奖惩"""
import json

class TestRewardAPI:
    def test_rewards_page(self, auth_client):
        resp = auth_client.get('/rewards')
        assert resp.status_code == 200

    def test_create(self, auth_client):
        auth_client.post('/add', data={'student_id':'R999','name':'奖惩生','enrollment_year':'2024'})
        resp = auth_client.post('/api/rewards_punishments', json={'student_id':'R999','rp_type':'奖励','title':'优秀','level':'校级','date':'2025-01-01','reason':'成绩优异','issuing_authority':'学生处'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list(self, auth_client):
        resp = auth_client.get('/api/rewards_punishments')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_list_with_filters(self, auth_client):
        auth_client.post('/add', data={'student_id':'R998','name':'奖惩生二','enrollment_year':'2024'})
        auth_client.post('/api/rewards_punishments', json={'student_id':'R998','rp_type':'奖励','title':'优秀','date':'2025-01-01','reason':'成绩优异'})
        resp = auth_client.get('/api/rewards_punishments?filters=[{"field":"rp_type","op":"eq","value":"奖励"}]')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_update(self, auth_client):
        auth_client.post('/add', data={'student_id':'R997','name':'奖惩生三','enrollment_year':'2024'})
        auth_client.post('/api/rewards_punishments', json={'student_id':'R997','rp_type':'奖励','title':'原标题','date':'2025-01-01','reason':'原因'})
        resp = auth_client.put('/api/rewards_punishments/1', json={'title':'新标题'})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_delete(self, auth_client):
        auth_client.post('/add', data={'student_id':'R996','name':'奖惩生四','enrollment_year':'2024'})
        auth_client.post('/api/rewards_punishments', json={'student_id':'R996','rp_type':'处分','title':'警告','date':'2025-01-01','reason':'原因'})
        resp = auth_client.delete('/api/rewards_punishments/1')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_student_rewards(self, auth_client):
        auth_client.post('/add', data={'student_id':'R995','name':'奖惩生五','enrollment_year':'2024'})
        auth_client.post('/api/rewards_punishments', json={'student_id':'R995','rp_type':'奖励','title':'标兵','date':'2025-01-01','reason':'原因'})
        resp = auth_client.get('/api/students/R995/rewards_punishments')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_teaching_students(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        resp = c.get('/api/teaching/1/students')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_set_score(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        resp = c.put('/api/enrollment/1/score', json={'score': 90})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_batch_score(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        resp = c.post('/api/enrollment/batch_score', json={'scores': [{'enroll_id': 1, 'score': 85}]})
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_student_scores(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        c.put('/api/enrollment/1/score', json={'score': 90})
        resp = c.get('/api/students/2024001/scores')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_score_stats(self, populated_db_full):
        c = populated_db_full
        c.post('/api/enrollment', json={"student_id":"2024001","teaching_id":1})
        c.put('/api/enrollment/1/score', json={'score': 90})
        resp = c.get('/api/teaching/1/score_stats')
        data = json.loads(resp.data)
        assert data['code'] == 0
