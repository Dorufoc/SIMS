"""综合查询 API"""
from flask import Blueprint, request, jsonify, render_template
from service.comprehensive_query_service import ComprehensiveQueryService, TABLE_LABELS
from middleware.auth_middleware import require_login

query_bp = Blueprint('query', __name__)


@query_bp.route('/query')
def query_page():
    """综合查询页面"""
    return render_template('query.html')


@query_bp.route('/api/query/comprehensive/tables', methods=['GET'])
@require_login
def comprehensive_tables():
    """获取所有业务数据表列表（主表选择用）"""
    svc = ComprehensiveQueryService()
    try:
        tables = svc.get_tables()
        return jsonify({'ok': True, 'data': tables})
    finally:
        svc.close()


@query_bp.route('/api/query/comprehensive/table/<table_name>/fields', methods=['GET'])
@require_login
def comprehensive_table_fields(table_name):
    """获取指定表的所有字段"""
    svc = ComprehensiveQueryService()
    try:
        fields = svc.get_table_fields(table_name)
        if not fields:
            return jsonify({'ok': False, 'error': f'表 {table_name} 不存在或不是业务表'}), 404
        return jsonify({'ok': True, 'data': fields})
    finally:
        svc.close()


@query_bp.route('/api/query/comprehensive/table/<table_name>/relations', methods=['GET'])
@require_login
def comprehensive_table_relations(table_name):
    """获取指定表的所有外键关联关系"""
    svc = ComprehensiveQueryService()
    try:
        relations = svc.get_table_relations(table_name)
        return jsonify({'ok': True, 'data': relations})
    finally:
        svc.close()


@query_bp.route('/api/query/comprehensive/execute', methods=['POST'])
@require_login
def comprehensive_execute():
    """执行综合联合查询"""
    data = request.get_json(silent=True) or {}
    main_table = data.get('main_table', '')
    selected_joins = data.get('joins', [])
    filters = data.get('filters', [])
    page = data.get('page', 1)

    if not main_table:
        return jsonify({'ok': False, 'error': '请选择主表'}), 400
    if main_table not in TABLE_LABELS:
        return jsonify({'ok': False, 'error': f'无效的主表: {main_table}'}), 400

    svc = ComprehensiveQueryService()
    try:
        result = svc.execute_query(main_table, selected_joins, filters, page)
        return jsonify(result)
    finally:
        svc.close()
