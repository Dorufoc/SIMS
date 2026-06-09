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

    svc = RewardService()
    try:
        items, total = svc.get_list(page, page_size)
        total_pages = (total + page_size - 1) // page_size
        data = [{'rp_id': r.rp_id, 'student_id': r.student_id, 'rp_type': r.rp_type,
                 'title': r.title, 'level': r.level, 'date': str(r.date),
                 'reason': r.reason, 'issuing_authority': r.issuing_authority, 'remark': r.remark} for r in items]
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
                    'title': data.get('title', ''), 'level': data.get('level', ''),
                    'date': data.get('date', ''), 'reason': data.get('reason', ''),
                    'issuing_authority': data.get('issuing_authority', ''),
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
                 'level': r.level, 'date': str(r.date), 'reason': r.reason} for r in rewards]
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
        success, msg = svc.batch_score(scores_data)
        if success:
            return jsonify({'code': 0, 'msg': msg})
        return jsonify({'code': 1, 'msg': msg})
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
