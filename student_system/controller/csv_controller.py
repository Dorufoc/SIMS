"""CSV 导入导出 API"""
from flask import Blueprint, request, jsonify, send_file
from service.csv_service import CSVService
from middleware.auth_middleware import require_login, csrf_protect
import logging

csv_bp = Blueprint('csv', __name__)


@csv_bp.route('/csv/template')
@require_login
def csv_template():
    svc = CSVService()
    try:
        template = svc.generate_template()
        output = template.getvalue().encode('utf-8-sig')
        from io import BytesIO
        return send_file(BytesIO(output), as_attachment=True,
                         download_name='student_template.csv', mimetype='text/csv')
    finally:
        svc.close()


@csv_bp.route('/csv/preview', methods=['POST'])
@require_login
@csrf_protect
def csv_preview():
    file = request.files.get('file')
    if not file:
        return jsonify({'valid_data': [], 'errors': ['请上传文件']})

    svc = CSVService()
    try:
        result = svc.parse_csv(file)
        return jsonify(result)
    finally:
        svc.close()


@csv_bp.route('/csv/import', methods=['POST'])
@require_login
@csrf_protect
def csv_import():
    data = request.get_json()
    valid_data = data.get('valid_data', [])

    svc = CSVService()
    try:
        count = svc.import_data(valid_data)
        return jsonify({'code': 0, 'msg': '导入成功', 'count': count})
    except Exception as e:
        logging.exception('导入CSV数据失败')
        return jsonify({'code': 1, 'msg': '导入失败，请检查数据格式'})
    finally:
        svc.close()


@csv_bp.route('/csv/export')
@require_login
def csv_export():
    svc = CSVService()
    try:
        csv_output = svc.export_csv()
        from io import BytesIO
        output = csv_output.getvalue().encode('utf-8-sig')
        return send_file(BytesIO(output), as_attachment=True,
                         download_name='student_data.csv', mimetype='text/csv')
    finally:
        svc.close()


@csv_bp.route('/csv/export_filtered', methods=['GET', 'POST'])
@require_login
@csrf_protect
def csv_export_filtered():
    svc = CSVService()
    try:
        csv_output = svc.export_csv()
        from io import BytesIO
        output = csv_output.getvalue().encode('utf-8-sig')
        return send_file(BytesIO(output), as_attachment=True,
                         download_name='student_data.csv', mimetype='text/csv')
    finally:
        svc.close()
