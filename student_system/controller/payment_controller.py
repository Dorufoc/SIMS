"""缴费管理 API"""
from flask import Blueprint, request, jsonify
from service.payment_service import PaymentService
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/api/payments', methods=['GET'])
@require_login
def api_payments():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    svc = PaymentService()
    try:
        items, total = svc.get_list(page, page_size)
        total_pages = (total + page_size - 1) // page_size
        data = [{'payment_id': p.payment_id, 'student_id': p.student_id, 'fee_type': p.fee_type,
                 'academic_year': p.academic_year, 'semester': p.semester,
                 'amount_due': float(p.amount_due or 0), 'amount_paid': float(p.amount_paid or 0),
                 'payment_date': str(p.payment_date) if p.payment_date else None,
                 'status': p.status, 'payment_method': p.payment_method, 'remark': p.remark} for p in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@payment_bp.route('/api/payments', methods=['POST'])
@require_admin
@csrf_protect
def api_create_payment():
    data = request.get_json()
    svc = PaymentService()
    try:
        svc.create({'student_id': data.get('student_id', ''), 'fee_type': data.get('fee_type', ''),
                    'academic_year': data.get('academic_year', ''), 'semester': data.get('semester', ''),
                    'amount_due': data.get('amount_due', 0)})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except Exception as e:
        logging.exception('创建缴费记录失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@payment_bp.route('/api/payments/<int:payment_id>/pay', methods=['POST'])
@require_admin
@csrf_protect
def api_pay(payment_id):
    data = request.get_json()
    svc = PaymentService()
    try:
        success, msg = svc.pay(payment_id, data.get('amount', 0), data.get('method', ''))
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@payment_bp.route('/api/payments/overdue', methods=['GET'])
@require_login
def api_overdue():
    svc = PaymentService()
    try:
        payments = svc.get_overdue()
        data = [{'payment_id': p.payment_id, 'student_id': p.student_id, 'fee_type': p.fee_type,
                 'amount_due': float(p.amount_due or 0), 'amount_paid': float(p.amount_paid or 0),
                 'status': p.status} for p in payments]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@payment_bp.route('/api/payments/stats', methods=['GET'])
@require_login
def api_payment_stats():
    svc = PaymentService()
    try:
        stats = svc.get_stats()
        return jsonify({'code': 0, 'data': stats})
    finally:
        svc.close()
