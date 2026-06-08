"""高级查询 API"""
from flask import Blueprint, request, jsonify, render_template, send_file, session
from service.query_service import QueryService
from service.csv_service import CSVService
from middleware.auth_middleware import require_login, csrf_protect
import io

query_bp = Blueprint('query', __name__)


@query_bp.route('/query')
def query_page():
    return render_template('query.html')


@query_bp.route('/query/build', methods=['POST'])
@require_login
@csrf_protect
def query_build():
    data = request.get_json()
    conditions = data.get('conditions', [])
    do_export = data.get('export', False)

    if not conditions:
        return jsonify({'sql': '', 'columns': [], 'data': []})

    svc = QueryService()
    try:
        rows = svc.dynamic_query(conditions)
        columns = []
        if rows:
            columns = [c for c in rows[0].__table__.columns.keys()] if hasattr(rows[0], '__table__') else []

        if do_export:
            csv_svc = CSVService()
            try:
                output = csv_svc.export_csv(query_results=rows)
                return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                                 as_attachment=True, download_name='student_data.csv', mimetype='text/csv')
            finally:
                csv_svc.close()

        data_list = []
        for r in rows:
            item = {}
            for c in r.__table__.columns.keys():
                item[c] = str(getattr(r, c, ''))
            data_list.append(item)

        return jsonify({'sql': '', 'columns': columns, 'data': data_list})
    finally:
        svc.close()


@query_bp.route('/query/filter', methods=['POST'])
def query_filter():
    """筛选查询 —— 前端 filterModule 调用的统一入口"""
    data = request.get_json()
    filters = data.get('filters', [])
    page = data.get('page', 1)

    # 转换前端筛选格式为内部格式
    conditions = []
    for f in filters:
        field = f.get('field', '')
        operator = f.get('operator', 'eq')
        value = f.get('value', '')

        # 前端字段名到内部字段名的映射
        field_map = {
            'student_id': 'student_id', 'student_name': 'name',
            'gender': 'gender', 'birth_date': 'birth_date',
            'class_name': 'class_name', 'major_name': 'major_name',
            'dept_name': 'dept_name', 'enrollment_year': 'enrollment_year',
            'phone': 'phone', 'email': 'email', 'status': 'status'
        }
        internal_field = field_map.get(field, field)

        # 运算符映射
        op_map = {'eq': '=', 'neq': '!=', 'gt': '>', 'gte': '>=', 'lt': '<',
                  'lte': '<=', 'contains': 'LIKE', 'startswith': 'LIKE', 'endswith': 'LIKE',
                  'in': 'IN', 'between': 'BETWEEN'}
        internal_op = op_map.get(operator, '=')

        cond = {'field': internal_field, 'operator': internal_op, 'value': value}
        if operator == 'startswith':
            cond['value'] = f'{value}%'
        elif operator == 'endswith':
            cond['value'] = f'%{value}'
        elif operator == 'contains':
            cond['value'] = f'%{value}%'
        conditions.append(cond)

    svc = QueryService()
    try:
        rows = svc.dynamic_query(conditions)
        if not rows:
            return jsonify({'ok': True, 'sql': '', 'columns': [], 'data': [], 'page': page, 'total_pages': 0})

        columns = [c for c in rows[0].__table__.columns.keys()] if hasattr(rows[0], '__table__') else []
        data_list = []
        for r in rows:
            item = {}
            for c_key in columns:
                val = getattr(r, c_key, None)
                item[c_key] = str(val) if val is not None else ''
            data_list.append(item)

        return jsonify({'ok': True, 'sql': '', 'columns': columns, 'data': data_list, 'page': page, 'total_pages': 1})
    finally:
        svc.close()


@query_bp.route('/query/scene', methods=['POST'])
def query_scene():
    """场景化查询"""
    data = request.get_json()
    scene = data.get('scene', '')
    params = data.get('params', {})

    conditions = []
    # 根据场景构建查询条件
    if scene == 'by_student_no':
        if params.get('val1'):
            conditions.append({'field': 'student_id', 'operator': '=', 'value': params['val1']})
    elif scene == 'by_student_name':
        if params.get('val1'):
            conditions.append({'field': 'name', 'operator': '=', 'value': params['val1']})
    elif scene == 'by_major':
        if params.get('val1'):
            conditions.append({'field': 'major_name', 'operator': 'LIKE', 'value': f'%{params["val1"]}%'})
    elif scene == 'by_dept':
        if params.get('val1'):
            conditions.append({'field': 'dept_name', 'operator': 'LIKE', 'value': f'%{params["val1"]}%'})
    elif scene == 'by_grade':
        if params.get('val1'):
            conditions.append({'field': 'enrollment_year', 'operator': '=', 'value': params['val1']})
    elif scene == 'by_age_range':
        if params.get('val1') and params.get('val2'):
            conditions.append({'field': 'birth_date', 'operator': 'BETWEEN', 'value': '', 'value_to': ''})
            # Between on birth_date needs date calculation - skip for now
            pass
    elif scene == 'by_gender':
        if params.get('val1'):
            conditions.append({'field': 'gender', 'operator': '=', 'value': 'M' if params['val1'] == '男' else 'F'})
    elif scene == 'by_class':
        if params.get('val1'):
            conditions.append({'field': 'class_name', 'operator': 'LIKE', 'value': f'%{params["val1"]}%'})
    elif scene == 'by_name_like':
        if params.get('val1'):
            conditions.append({'field': 'name', 'operator': 'LIKE', 'value': f'%{params["val1"]}%'})
    elif scene == 'not_dept':
        if params.get('val1'):
            conditions.append({'field': 'dept_name', 'operator': '!=', 'value': params['val1']})
    elif scene == 'by_not_major':
        if params.get('val1'):
            conditions.append({'field': 'major_name', 'operator': '!=', 'value': params['val1']})

    svc = QueryService()
    try:
        if conditions:
            rows = svc.dynamic_query(conditions)
        else:
            rows = []

        desc = f'场景查询: {scene}'
        if not rows:
            return jsonify({'desc': desc, 'sql': '', 'columns': [], 'data': []})

        columns = [c for c in rows[0].__table__.columns.keys()] if hasattr(rows[0], '__table__') else []
        data_list = []
        for r in rows:
            item = {}
            for c_key in columns:
                val = getattr(r, c_key, None)
                item[c_key] = str(val) if val is not None else ''
            data_list.append(item)

        return jsonify({'desc': desc, 'sql': '', 'columns': columns, 'data': data_list})
    finally:
        svc.close()


@query_bp.route('/query/keyword', methods=['GET'])
def query_keyword_detail():
    """获取 SQL 关键词详情"""
    keyword = request.args.get('keyword', '')
    # 返回关键词定义和示例
    keywords_info = {
        'SELECT': {'description': 'SELECT 用于从数据库中选取数据', 'sql': 'SELECT column1, column2 FROM table_name;', 'executable': False},
        'FROM': {'description': 'FROM 指定要查询的表', 'sql': 'SELECT * FROM students;', 'executable': False},
        'WHERE': {'description': 'WHERE 用于过滤记录', 'sql': 'SELECT * FROM students WHERE grade > 80;', 'executable': False},
        'GROUP BY': {'description': 'GROUP BY 用于对结果集进行分组', 'sql': 'SELECT major, COUNT(*) FROM students GROUP BY major;', 'executable': False},
        'HAVING': {'description': 'HAVING 用于过滤分组后的结果', 'sql': 'SELECT major, COUNT(*) FROM students GROUP BY major HAVING COUNT(*) > 5;', 'executable': False},
        'ORDER BY': {'description': 'ORDER BY 用于对结果集排序', 'sql': 'SELECT * FROM students ORDER BY name ASC;', 'executable': False},
        'JOIN': {'description': 'JOIN 用于连接多张表', 'sql': 'SELECT s.name, c.class_name FROM students s JOIN classes c ON s.class_id = c.class_id;', 'executable': False},
        'INSERT': {'description': 'INSERT 用于插入新记录', 'sql': "INSERT INTO students (student_id, name) VALUES ('2024001', '张三');", 'executable': True},
        'UPDATE': {'description': 'UPDATE 用于修改现有记录', 'sql': "UPDATE students SET phone = '13800000000' WHERE student_id = '2024001';", 'executable': True},
        'DELETE': {'description': 'DELETE 用于删除记录', 'sql': "DELETE FROM students WHERE student_id = '2024001';", 'executable': True},
        'DROP TABLE': {'description': 'DROP TABLE 删除整张表（危险操作）', 'sql': 'DROP TABLE IF EXISTS temp_table;', 'executable': True},
        'DROP DATABASE': {'description': 'DROP DATABASE 删除整个数据库（极度危险操作）', 'sql': 'DROP DATABASE IF EXISTS temp_db;', 'executable': True},
    }
    info = keywords_info.get(keyword, {'description': '暂未收录该关键词', 'sql': '', 'executable': False})
    info['keyword'] = keyword
    return jsonify(info)


@query_bp.route('/query/keyword/execute', methods=['POST'])
def query_keyword_execute():
    """执行关键词对应的 SQL 示例"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    
    # 只有管理员可以执行危险操作
    dangerous = ['DROP_TABLE', 'DROP_DATABASE']
    if keyword in dangerous and session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': '仅管理员可执行此操作'})
    
    return jsonify({'success': True, 'message': f'关键词 {keyword} 的操作已记录'})


@query_bp.route('/query/stat', methods=['POST'])
@require_login
@csrf_protect
def query_stat():
    return _stat_query()


@query_bp.route('/query/stat-with-params', methods=['POST'])
@require_login
@csrf_protect
def query_stat_with_params():
    return _stat_query()


def _stat_query():
    """统计查询 -- 返回学生列表数据"""
    from service.statistics_service import StatisticsService
    svc = StatisticsService()
    try:
        data = {
            'by_dept': [{'name': r[0], 'count': r[1]} for r in svc.student_by_dept()],
            'by_major': [{'name': r[0], 'count': r[1]} for r in svc.student_by_major()],
            'by_class': [{'name': r[0], 'count': r[1]} for r in svc.student_by_class()],
            'by_year': [{'year': str(r[0]), 'count': r[1]} for r in svc.student_by_enrollment_year()],
        }
        return jsonify({'sql': '', 'columns': ['category', 'count'], 'data': data})
    finally:
        svc.close()


@query_bp.route('/query/sort', methods=['POST'])
@require_login
@csrf_protect
def query_sort():
    data = request.get_json()
    page = data.get('page', 1)
    sort_fields = data.get('sort_fields', [])

    if not sort_fields:
        sort_field = data.get('sort_field', 'student_id')
        sort_order = data.get('sort_order', 'asc')
        sort_field_2 = data.get('sort_field_2', '')
        sort_order_2 = data.get('sort_order_2', 'asc')
        if sort_field:
            sort_fields.append({'field': sort_field, 'order': sort_order})
        if sort_field_2:
            sort_fields.append({'field': sort_field_2, 'order': sort_order_2})

    if not sort_fields:
        sort_fields = [{'field': 'student_id', 'order': 'asc'}]

    svc = QueryService()
    try:
        items, total = svc.sort_query(sort_fields, page, 10)
        total_pages = (total + 10 - 1) // 10 if total > 0 else 0

        data_list = []
        for item in items:
            d = {}
            if hasattr(item, '__table__'):
                for c in item.__table__.columns.keys():
                    d[c] = str(getattr(item, c, ''))
            data_list.append(d)

        return jsonify({'sql': '', 'columns': list(data_list[0].keys()) if data_list else [],
                        'data': data_list, 'total': total, 'page': page, 'total_pages': total_pages})
    finally:
        svc.close()
