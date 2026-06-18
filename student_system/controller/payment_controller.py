"""缴费管理 API"""
from flask import Blueprint, request, jsonify, render_template
from service.payment_service import PaymentService
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/payments')
def payments_page():
    return render_template('payments.html')


@payment_bp.route('/api/payments', methods=['GET'])
@require_login
def api_payments():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')

    svc = PaymentService()
    try:
        from sqlalchemy.orm import joinedload
        from entity.payment import Payment

        SORT_FIELDS = {
            'payment_id': Payment.payment_id,
            'student_id': Payment.student_id,
            'fee_type': Payment.fee_type,
            'academic_year': Payment.academic_year,
            'semester': Payment.semester,
            'amount_due': Payment.amount_due,
            'amount_paid': Payment.amount_paid,
            'payment_date': Payment.payment_date,
            'status': Payment.status,
            'payment_method': Payment.payment_method,
        }
        sort_by = request.args.get('sort_by', '')
        sort_order = request.args.get('sort_order', '')
        order_col = SORT_FIELDS.get(sort_by)
        if order_col is not None:
            if sort_order == 'desc':
                order_col = order_col.desc()
        else:
            order_col = Payment.payment_id.desc()

        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []
            items, total = svc.repo.filter_paginate(filters, page, page_size, order_col)
        else:
            q = svc.repo.db.query(svc.repo.model).options(
                joinedload(svc.repo.model.student)
            )
            q = q.order_by(order_col)
            items, total = svc.repo.paginate(page, page_size, q)

        total_pages = (total + page_size - 1) // page_size
        data = [{'payment_id': p.payment_id, 'student_id': p.student_id,
                 'student_name': p.student.name if p.student else '',
                 'fee_type': p.fee_type,
                 'academic_year': p.academic_year, 'semester': p.semester,
                 'amount_due': float(p.amount_due or 0), 'amount_paid': float(p.amount_paid or 0),
                 'payment_date': str(p.payment_date) if p.payment_date else None,
                 'status': p.status, 'payment_method': p.payment_method, 'remark': p.remark} for p in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    except Exception as e:
        logging.exception('获取缴费列表失败')
        return jsonify({'code': 1, 'msg': '获取缴费列表失败，请稍后重试'}), 500
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
    except Exception as e:
        logging.exception('登记缴费失败')
        return jsonify({'code': 1, 'msg': '缴费失败，请稍后重试'}), 500
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
    except Exception as e:
        logging.exception('获取欠费列表失败')
        return jsonify({'code': 1, 'msg': '获取欠费列表失败'}), 500
    finally:
        svc.close()


@payment_bp.route('/api/payments/stats', methods=['GET'])
@require_login
def api_payment_stats():
    svc = PaymentService()
    try:
        stats = svc.get_stats()
        return jsonify({'code': 0, 'data': stats})
    except Exception as e:
        logging.exception('获取缴费统计失败')
        return jsonify({'code': 1, 'msg': '获取缴费统计失败'}), 500
    finally:
        svc.close()
