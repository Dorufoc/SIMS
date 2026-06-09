"""批量导入导出 API —— 通用控制器，支持所有实体类型"""
from flask import Blueprint, request, jsonify, send_file
from service.batch_import_service import BatchImportService
from service.batch_import_configs import *  # noqa: F401 F403 触发配置注册
from middleware.auth_middleware import require_login, csrf_protect
import logging

csv_bp = Blueprint('csv', __name__)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# 通用批量导入 API  ── /api/import/<entity_type>/...
# ═══════════════════════════════════════════

@csv_bp.route('/api/import/<entity_type>/template')
@require_login
def batch_template(entity_type: str):
    """下载指定实体的 CSV 导入模板"""
    try:
        cfg = BatchImportService.get_config(entity_type)
        if not cfg:
            return jsonify({'code': 1, 'msg': f'不支持的实体类型: {entity_type}'}), 400
        output = BatchImportService.generate_template(entity_type)
        data = output.getvalue().encode('utf-8-sig')
        from io import BytesIO
        return send_file(BytesIO(data), as_attachment=True,
                         download_name=f'{entity_type}_template.csv', mimetype='text/csv')
    except Exception as e:
        logger.exception(f'生成模板失败 [{entity_type}]')
        return jsonify({'code': 1, 'msg': str(e)}), 500


@csv_bp.route('/api/import/<entity_type>/import', methods=['POST'])
@require_login
@csrf_protect
def batch_import(entity_type: str):
    """批量导入数据到指定实体"""
    try:
        cfg = BatchImportService.get_config(entity_type)
        if not cfg:
            return jsonify({'code': 1, 'msg': f'不支持的实体类型: {entity_type}'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'msg': '请求数据为空'}), 400

        valid_data = data.get('data', data.get('valid_data', []))
        if not valid_data:
            return jsonify({'code': 1, 'msg': '没有有效数据可导入'}), 400

        count = BatchImportService.import_data(entity_type, valid_data)
        return jsonify({'code': 0, 'msg': '导入成功', 'count': count})
    except Exception as e:
        logger.exception(f'批量导入失败 [{entity_type}]')
        return jsonify({'code': 1, 'msg': f'导入失败：{e}'}), 500


@csv_bp.route('/api/import/<entity_type>/export')
@require_login
def batch_export(entity_type: str):
    """导出指定实体的所有数据为 CSV"""
    try:
        cfg = BatchImportService.get_config(entity_type)
        if not cfg:
            return jsonify({'code': 1, 'msg': f'不支持的实体类型: {entity_type}'}), 400

        output = BatchImportService.export_data(entity_type)
        data = output.getvalue().encode('utf-8-sig')
        from io import BytesIO
        return send_file(BytesIO(data), as_attachment=True,
                         download_name=f'{entity_type}_data.csv', mimetype='text/csv')
    except Exception as e:
        logger.exception(f'导出失败 [{entity_type}]')
        return jsonify({'code': 1, 'msg': str(e)}), 500


# ═══════════════════════════════════════════
# 兼容旧版 API  ── /csv/...  (默认指向 student)
# ═══════════════════════════════════════════

@csv_bp.route('/csv/template')
@require_login
def csv_template():
    """下载学生 CSV 模板（兼容旧版）"""
    try:
        output = BatchImportService.generate_template('student')
        data = output.getvalue().encode('utf-8-sig')
        from io import BytesIO
        return send_file(BytesIO(data), as_attachment=True,
                         download_name='student_template.csv', mimetype='text/csv')
    except Exception as e:
        logger.exception('生成学生模板失败')
        return jsonify({'code': 1, 'msg': str(e)}), 500


@csv_bp.route('/csv/preview', methods=['POST'])
@require_login
@csrf_protect
def csv_preview():
    """CSV 预览（兼容旧版）"""
    file = request.files.get('file')
    if not file:
        return jsonify({'valid_data': [], 'errors': ['请上传文件']})

    try:
        result = BatchImportService.parse_csv('student', file)
        return jsonify(result)
    except Exception as e:
        logger.exception('CSV 预览失败')
        return jsonify({'valid_data': [], 'errors': [str(e)]})


@csv_bp.route('/csv/import', methods=['POST'])
@require_login
@csrf_protect
def csv_import():
    """批量导入学生数据（兼容旧版）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'msg': '请求数据为空'}), 400

        valid_data = data.get('data', data.get('valid_data', []))
        if not valid_data:
            return jsonify({'code': 1, 'msg': '没有有效数据可导入'}), 400

        count = BatchImportService.import_data('student', valid_data)
        return jsonify({'code': 0, 'msg': '导入成功', 'count': count})
    except Exception as e:
        logger.exception('导入CSV数据失败')
        return jsonify({'code': 1, 'msg': f'导入失败，请检查数据格式'}), 500


@csv_bp.route('/csv/export')
@require_login
def csv_export():
    """导出学生数据（兼容旧版）"""
    try:
        output = BatchImportService.export_data('student')
        data = output.getvalue().encode('utf-8-sig')
        from io import BytesIO
        return send_file(BytesIO(data), as_attachment=True,
                         download_name='student_data.csv', mimetype='text/csv')
    except Exception as e:
        logger.exception('导出失败')
        return jsonify({'code': 1, 'msg': str(e)}), 500


