"""统计 API"""
from flask import Blueprint, request, jsonify, render_template
from service.statistics_service import StatisticsService
from middleware.auth_middleware import require_login

statistics_bp = Blueprint('statistics', __name__)


@statistics_bp.route('/statistics')
def statistics_page():
    return render_template('statistics.html')


@statistics_bp.route('/api/statistics/dashboard', methods=['GET'])
@require_login
def api_dashboard():
    svc = StatisticsService()
    try:
        data = svc.dashboard()
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@statistics_bp.route('/api/statistics/students', methods=['GET'])
@require_login
def api_student_stats():
    svc = StatisticsService()
    try:
        data = {
            'by_dept': [{'name': r[0], 'count': r[1]} for r in svc.student_by_dept()],
            'by_major': [{'name': r[0], 'count': r[1]} for r in svc.student_by_major()],
            'by_class': [{'name': r[0], 'count': r[1]} for r in svc.student_by_class()],
            'by_year': [{'year': r[0], 'count': r[1]} for r in svc.student_by_enrollment_year()],
        }
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@statistics_bp.route('/api/statistics/gender', methods=['GET'])
@require_login
def api_gender_stats():
    svc = StatisticsService()
    try:
        results = svc.gender_distribution()
        data = [{'gender': '男' if r[0] == 'M' else ('女' if r[0] == 'F' else '未知'), 'count': r[1]} for r in results]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@statistics_bp.route('/api/statistics/student_status', methods=['GET'])
@require_login
def api_student_status():
    svc = StatisticsService()
    try:
        results = svc.student_status()
        data = [{'status': r[0], 'count': r[1]} for r in results]
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@statistics_bp.route('/api/statistics/grades', methods=['GET'])
@require_login
def api_grade_stats():
    teaching_id = request.args.get('teaching_id', type=int)
    svc = StatisticsService()
    try:
        data = svc.grade_distribution(teaching_id)
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@statistics_bp.route('/api/statistics/class_grades', methods=['GET'])
@require_login
def api_class_grade_stats():
    from service.statistics_service import StatisticsService as SS
    svc = SS()
    try:
        data = svc.grade_distribution()
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()


@statistics_bp.route('/api/statistics/gpa_ranking', methods=['GET'])
@require_login
def api_gpa_ranking():
    limit = request.args.get('limit', 50, type=int)
    svc = StatisticsService()
    try:
        data = svc.gpa_ranking(limit)
        return jsonify({'code': 0, 'data': data})
    finally:
        svc.close()
