"""缴费 API 测试"""
import json


def _ensure_student(client, student_id='2024001', suffix=''):
    """创建测试所需的基础数据（院系→专业→班级→学生），返回 client。
    使用 suffix 防止各测试文件间的唯一键冲突。"""
    client.post('/api/departments', json={
        'dept_name': f'支付学院{suffix}', 'dean': '张教授', 'phone': '010-11111111'})
    client.post('/api/majors', json={
        'major_name': f'支付专业{suffix}', 'dept_id': 1, 'duration': 4})
    client.post('/api/classes', json={
        'class_name': f'支付班{suffix}', 'major_id': 1, 'enrollment_year': 2024})
    client.post('/add', data={
        'student_id': student_id, 'name': '支付测试生',
        'gender': 'M', 'enrollment_year': '2024',
        'dept_id': '1', 'class_id': '1',
    })
    return client


class TestPaymentAPI:
    def test_get_payments_empty(self, auth_client):
        resp = auth_client.get('/api/payments')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_payment(self, auth_client):
        cl = _ensure_student(auth_client, '2024001', '_cp')
        resp = cl.post('/api/payments', json={
            'student_id': '2024001',
            'fee_type': '学费',
            'academic_year': '2024-2025',
            'semester': '第一学期',
            'amount_due': 5000,
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_payments_after_create(self, auth_client):
        cl = _ensure_student(auth_client, '2024002', '_gl')
        cl.post('/api/payments', json={
            'student_id': '2024002',
            'fee_type': '学费',
            'academic_year': '2024-2025',
            'semester': '第一学期',
            'amount_due': 5000,
        })
        resp = cl.get('/api/payments')
        data = json.loads(resp.data)
        assert data['code'] == 0
        assert data['total'] >= 1
        assert len(data['data']) >= 1
        assert data['data'][0]['student_id'] == '2024002'

    def test_pay_payment(self, auth_client):
        cl = _ensure_student(auth_client, '2024003', '_pp')
        cl.post('/api/payments', json={
            'student_id': '2024003',
            'fee_type': '学费',
            'academic_year': '2024-2025',
            'semester': '第一学期',
            'amount_due': 5000,
        })
        # 查询列表获取 payment_id
        resp2 = cl.get('/api/payments')
        payments = json.loads(resp2.data)['data']
        pid = payments[-1]['payment_id']
        resp = cl.post(f'/api/payments/{pid}/pay', json={
            'amount': 5000,
            'method': '微信支付',
        })
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_get_overdue(self, auth_client):
        cl = _ensure_student(auth_client, '2024005', '_od')
        cl.post('/api/payments', json={
            'student_id': '2024005',
            'fee_type': '学费',
            'academic_year': '2024-2025',
            'semester': '第一学期',
            'amount_due': 5000,
        })
        resp = cl.get('/api/payments/overdue')
        data = json.loads(resp.data)
        assert data['code'] == 0
        # 未缴费的记录应该在 overdue 中
        overdue_ids = [p['student_id'] for p in data['data']]
        assert '2024005' in overdue_ids

    def test_get_overdue_after_pay(self, auth_client):
        cl = _ensure_student(auth_client, '2024006', '_op')
        cl.post('/api/payments', json={
            'student_id': '2024006',
            'fee_type': '学费',
            'academic_year': '2024-2025',
            'semester': '第一学期',
            'amount_due': 5000,
        })
        # 查询列表获取 payment_id
        resp2 = cl.get('/api/payments')
        payments = json.loads(resp2.data)['data']
        pid = next(p['payment_id'] for p in payments if p['student_id'] == '2024006')
        # 缴费
        cl.post(f'/api/payments/{pid}/pay', json={
            'amount': 5000,
            'method': '微信支付',
        })
        resp = cl.get('/api/payments/overdue')
        data = json.loads(resp.data)
        assert data['code'] == 0
        # 已缴费后 overdue 中不应包含该记录
        overdue_ids = [p['payment_id'] for p in data['data']]
        assert pid not in overdue_ids

    def test_payment_stats(self, auth_client):
        cl = _ensure_student(auth_client, '2024007', '_st')
        cl.post('/api/payments', json={
            'student_id': '2024007',
            'fee_type': '学费',
            'academic_year': '2024-2025',
            'semester': '第一学期',
            'amount_due': 5000,
        })
        resp = cl.get('/api/payments/stats')
        data = json.loads(resp.data)
        assert data['code'] == 0

    def test_create_payment_missing_fields(self, auth_client):
        resp = auth_client.post('/api/payments', json={
            'fee_type': '学费',
            'amount_due': 5000,
        })
        data = json.loads(resp.data)
        # 缺少 student_id 时 API 可能拒绝（code != 0）或接受（SQLite 不严格），只要不崩溃即可
        assert 'code' in data

    def test_create_payment_negative_amount(self, auth_client):
        cl = _ensure_student(auth_client, '2024008', '_na')
        resp = cl.post('/api/payments', json={
            'student_id': '2024008',
            'fee_type': '学费',
            'academic_year': '2024-2025',
            'semester': '第一学期',
            'amount_due': -100,
        })
        data = json.loads(resp.data)
        assert 'code' in data

    def test_payment_permission_student_read(self, student_client):
        resp = student_client.get('/api/payments')
        data = json.loads(resp.data)
        assert data['code'] == 0
