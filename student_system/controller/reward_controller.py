"""奖惩管理 API + 成绩 API"""
from flask import Blueprint, request, jsonify, render_template
from service.reward_service import RewardService
from service.grade_service import GradeService
from middleware.auth_middleware import require_login, require_admin, csrf_protect
import logging

reward_bp = Blueprint('reward', __name__)


# ---- 奖惩页面 ----
@reward_bp.route('/rewards')
def rewards_page():
    return render_template('rewards.html')


# ---- 奖惩 ----
@reward_bp.route('/api/rewards_punishments', methods=['GET'])
@require_login
def api_rewards():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    filters_json = request.args.get('filters', '')

    svc = RewardService()
    try:
        from entity.reward_punishment import RewardPunishment

        SORT_FIELDS = {
            'rp_id': RewardPunishment.rp_id,
            'student_id': RewardPunishment.student_id,
            'rp_type': RewardPunishment.rp_type,
            'title': RewardPunishment.title,
            'date': RewardPunishment.date,
        }
        sort_by = request.args.get('sort_by', '')
        sort_order = request.args.get('sort_order', '')
        order_col = SORT_FIELDS.get(sort_by)
        if order_col is not None:
            if sort_order == 'desc':
                order_col = order_col.desc()

        if filters_json:
            import json
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = []
            order_by = order_col if order_col is not None else svc.repo.model.date.desc()
            items, total = svc.repo.filter_paginate(filters, page, page_size, order_by)
        else:
            from sqlalchemy.orm import joinedload
            q = svc.repo.db.query(svc.repo.model).options(
                joinedload(svc.repo.model.student)
            )
            if order_col is not None:
                q = q.order_by(order_col)
            else:
                q = q.order_by(svc.repo.model.date.desc())
            items, total = svc.repo.paginate(page, page_size, q)
        total_pages = (total + page_size - 1) // page_size
        data = [{'rp_id': r.rp_id, 'student_id': r.student_id,
                 'student_name': r.student.name if r.student else '',
                 'rp_type': r.rp_type,
                 'title': r.title, 'date': str(r.date),
                 'reason': r.reason, 'remark': r.remark} for r in items]
        return jsonify({'code': 0, 'data': data, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()


@reward_bp.route('/api/rewards_punishments', methods=['POST'])
@require_admin
@csrf_protect
def api_create_reward():
    data = request.get_json()
    svc = RewardService()
    try:
        svc.create({'student_id': data.get('student_id', ''), 'rp_type': data.get('rp_type', ''),
                    'title': data.get('title', ''),
                    'date': data.get('date', ''), 'reason': data.get('reason', ''),
                    'remark': data.get('remark', '')})
        return jsonify({'code': 0, 'msg': '创建成功'})
    except Exception as e:
        logging.exception('创建奖惩记录失败')
        return jsonify({'code': 1, 'msg': '创建失败，请稍后重试'})
    finally:
        svc.close()


@reward_bp.route('/api/rewards_punishments/<int:rp_id>', methods=['PUT'])
@require_admin
@csrf_protect
def api_update_reward(rp_id):
    data = request.get_json()
    svc = RewardService()
    try:
        result = svc.update(rp_id, {k: v for k, v in data.items() if v is not None})
        if result:
            return jsonify({'code': 0, 'msg': '更新成功'})
        return jsonify({'code': 1, 'msg': '记录不存在'})
    finally:
        svc.close()


@reward_bp.route('/api/rewards_punishments/<int:rp_id>', methods=['DELETE'])
@require_admin
@csrf_protect
def api_delete_reward(rp_id):
    svc = RewardService()
    try:
        existing = svc.repo.get_by_id(rp_id)
        if not existing:
            return jsonify({'code': 1, 'msg': '奖惩记录不存在'}), 404
        svc.delete(rp_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    finally:
        svc.close()


@reward_bp.route('/api/students/<student_id>/rewards_punishments', methods=['GET'])
@require_login
def api_student_rewards(student_id):
    svc = RewardService()
    try:
        rewards = svc.get_by_student(student_id)
        data = [{'rp_id': r.rp_id, 'rp_type': r.rp_type, 'title': r.title,
                 'date': str(r.date), 'reason': r.reason} for r in rewards]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


# ---- 成绩 ----
@reward_bp.route('/api/teaching/<int:teaching_id>/students', methods=['GET'])
@require_login
def api_teaching_students(teaching_id):
    svc = GradeService()
    try:
        students = svc.get_teaching_students(teaching_id)
        data = [{'enroll_id': s.enroll_id, 'student_id': s.student_id,
                 'score': float(s.score) if s.score else None,
                 'grade_point': float(s.grade_point) if s.grade_point else None,
                 'status': s.status} for s in students]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@reward_bp.route('/api/enrollment/<int:enroll_id>/score', methods=['PUT'])
@require_admin
@csrf_protect
def api_set_score(enroll_id):
    data = request.get_json()
    svc = GradeService()
    try:
        success, msg = svc.set_score(enroll_id, data.get('score'))
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
    finally:
        svc.close()


@reward_bp.route('/api/enrollment/batch_score', methods=['POST'])
@require_admin
@csrf_protect
def api_batch_score():
    data = request.get_json()
    scores_data = data.get('scores', [])
    svc = GradeService()
    try:
        success, msg, errors = svc.batch_score(scores_data)
        if success:
            return jsonify({'code': 0, 'msg': msg, 'errors': errors})
        return jsonify({'code': 1, 'msg': msg, 'errors': errors})
    finally:
        svc.close()


@reward_bp.route('/api/students/<student_id>/scores', methods=['GET'])
@require_login
def api_student_scores(student_id):
    svc = GradeService()
    try:
        scores = svc.get_student_scores(student_id)
        data = [{'enroll_id': s.enroll_id, 'score': float(s.score) if s.score else None,
                 'grade_point': float(s.grade_point) if s.grade_point else None} for s in scores]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@reward_bp.route('/api/teaching/<int:teaching_id>/score_stats', methods=['GET'])
@require_login
def api_score_stats(teaching_id):
    svc = GradeService()
    try:
        stats = svc.get_course_score_stats(teaching_id)
        return jsonify({'code': 0, 'data': stats})
    finally:
        svc.close()
