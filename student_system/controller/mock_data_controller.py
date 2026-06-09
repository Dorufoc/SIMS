"""模拟数据填充 API"""
from flask import Blueprint, request, jsonify, session
from service.mock_data_service import MockDataService
from middleware.auth_middleware import require_login

mock_data_bp = Blueprint('mock_data', __name__)


@mock_data_bp.route('/api/mock-data/generate', methods=['POST'])
@require_login
def api_generate_mock_data():
    """生成模拟数据"""
    if session.get('user_role') != 'admin':
        return jsonify({'code': 1, 'msg': '权限不足，仅管理员可操作'}), 403

    data = request.get_json(silent=True) or {}
    tables = data.get('tables', [])

    if not tables or not isinstance(tables, list):
        return jsonify({'code': 1, 'msg': '请提供要填充的表名列表'}), 400

    # 验证表名
    invalid = [t for t in tables if t not in MockDataService.VALID_TABLES]
    if invalid:
        return jsonify({'code': 1, 'msg': f'无效的表名: {", ".join(invalid)}'}), 400

    svc = MockDataService()
    try:
        result = svc.generate(tables)
        total = sum(result.values())
        table_msgs = []
        for tbl, cnt in result.items():
            if cnt > 0:
                table_msgs.append(f'{tbl} +{cnt}条')
        detail = ', '.join(table_msgs) if table_msgs else '没有新数据生成'
        return jsonify({
            'code': 0,
            'msg': f'成功生成 {total} 条数据',
            'data': {
                'total': total,
                'generated': result,
                'detail': detail,
            }
        })
    finally:
        svc.close()
