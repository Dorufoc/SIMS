"""通用批量导入服务 —— 支持任意实体的 CSV 模板生成、解析、导入、导出"""
import csv
import io
from datetime import date
from typing import Any, Dict, List, Optional, Callable


class BatchImportService:
    """通用批量导入服务，不绑定任何具体实体"""

    # ── 实体配置注册表 ──
    # 格式: { entity_type: { ... } }
    ENTITY_CONFIGS: Dict[str, dict] = {}

    @classmethod
    def register(cls, entity_type: str, **config):
        """注册一个实体类型的导入配置"""
        cls.ENTITY_CONFIGS[entity_type] = config

    @classmethod
    def get_config(cls, entity_type: str) -> Optional[dict]:
        return cls.ENTITY_CONFIGS.get(entity_type)

    @classmethod
    def all_entity_types(cls) -> List[str]:
        return list(cls.ENTITY_CONFIGS.keys())

    # ────────────────── 模板 ──────────────────

    @classmethod
    def generate_template(cls, entity_type: str) -> io.StringIO:
        """为指定实体生成 CSV 模板"""
        cfg = cls._require_config(entity_type)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cfg['template_headers'])
        if cfg.get('template_example'):
            writer.writerow(cfg['template_example'])
        output.seek(0)
        return output

    # ────────────────── 解析 ──────────────────

    @classmethod
    def parse_csv(cls, entity_type: str, file_stream) -> Dict[str, list]:
        """解析 CSV 文件，返回 {'valid_data': [...], 'errors': [...]}"""
        cfg = cls._require_config(entity_type)
        valid_data = []
        errors = []

        raw = file_stream.read()
        if isinstance(raw, bytes):
            content = raw.decode('utf-8-sig')
        else:
            content = raw

        lines = content.split('\n')
        if len(lines) > 10000:
            return {'valid_data': [], 'errors': ['文件行数超过限制（最多 10000 行）']}

        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return {'valid_data': [], 'errors': ['CSV 文件为空或无表头']}

        header_key = cfg.get('header_check_field')
        if header_key and header_key not in reader.fieldnames:
            return {'valid_data': [], 'errors': ['CSV 模板不正确，请使用标准模板']}

        field_map = cfg['field_map']
        required_fields = cfg.get('required_fields', [])
        on_parse_row: Optional[Callable] = cfg.get('on_parse_row')

        for i, row in enumerate(reader, start=2):
            try:
                item = {}
                row_errors = []

                for csv_col, entity_field in field_map.items():
                    raw_val = row.get(csv_col, '')
                    if raw_val is None:
                        raw_val = ''
                    raw_val = str(raw_val).strip()
                    item[entity_field] = raw_val if raw_val else None

                # 必填校验
                for rf in required_fields:
                    if not item.get(rf):
                        row_errors.append(f'第{i}行：{cfg.get("field_labels", {}).get(rf, rf)}不能为空')
                        break

                if row_errors:
                    errors.extend(row_errors)
                    continue

                # 自定义行解析（类型转换等）
                if on_parse_row:
                    parsed, parse_errors = on_parse_row(i, item, row)
                    errors.extend(parse_errors)
                    if parse_errors:
                        continue
                    item = parsed

                valid_data.append(item)

            except Exception as exc:
                errors.append(f'第{i}行：解析异常 - {exc}')

        return {'valid_data': valid_data, 'errors': errors}

    # ────────────────── 导入 ──────────────────

    @classmethod
    def import_data(cls, entity_type: str, valid_data: List[dict]) -> int:
        """将已验证的数据批量写入数据库。返回新增数量。"""
        cfg = cls._require_config(entity_type)
        repo = cfg['repo']()
        count = 0
        try:
            find_existing: Optional[Callable] = cfg.get('find_existing')
            create_entity: Callable = cfg.get('create_entity')

            for item in valid_data:
                # 去重：查找已存在记录
                existing = None
                if find_existing:
                    existing = find_existing(repo, item)

                if existing:
                    # 更新已存在记录
                    for k, v in item.items():
                        if v is not None and hasattr(existing, k):
                            setattr(existing, k, v)
                else:
                    # 创建新记录
                    if create_entity:
                        entity = create_entity(item)
                    else:
                        model = cfg['model']
                        entity = model(**{k: v for k, v in item.items() if hasattr(model, k)})
                    repo.db.add(entity)
                    count += 1

            repo.db.commit()
        except Exception:
            repo.db.rollback()
            raise
        finally:
            repo.close()
        return count

    # ────────────────── 导出 ──────────────────

    @classmethod
    def export_data(cls, entity_type: str, query_results=None) -> io.StringIO:
        """导出实体数据为 CSV"""
        cfg = cls._require_config(entity_type)
        repo = cfg['repo']()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cfg['export_headers'])

        try:
            data = query_results if query_results is not None else repo.get_all()
            export_row: Callable = cfg.get('export_row')
            for obj in data:
                writer.writerow(export_row(obj))
        finally:
            repo.close()

        output.seek(0)
        return output

    # ────────────────── helper ──────────────────

    @classmethod
    def _require_config(cls, entity_type: str) -> dict:
        cfg = cls.ENTITY_CONFIGS.get(entity_type)
        if not cfg:
            raise ValueError(f'未注册的实体类型: {entity_type}')
        return cfg
