"""综合查询服务

支持跨表 JOIN 查询、动态字段选择、多条件过滤和分页。
"""

from entity.base import SessionLocal, engine
from sqlalchemy import inspect as sa_inspect, text

# 业务表中文标签映射（排除 users, user_permissions）
TABLE_LABELS = {
    'students': '学生',
    'teachers': '教师',
    'classes': '班级',
    'majors': '专业',
    'departments': '院系',
    'courses': '课程',
    'teaching': '授课',
    'enrollments': '选课/成绩',
    'payments': '缴费',
    'dorm_rooms': '宿舍房间',
    'dorm_assignments': '住宿分配',
    'rewards_punishments': '奖惩',
    'semesters': '学期',
}

# 通用字段中文标签映射
FIELD_LABELS = {
    # IDs
    'student_id': '学号',
    'teacher_id': '教师编号',
    'course_id': '课程编号',
    'class_id': '班级编号',
    'major_id': '专业编号',
    'dept_id': '院系编号',
    'teaching_id': '授课编号',
    'enroll_id': '选课记录编号',
    'payment_id': '缴费编号',
    'assign_id': '分配编号',
    'room_id': '房间编号',
    'rp_id': '奖惩编号',
    'semester_id': '学期编号',
    'log_id': '日志编号',
    # 通用名称字段
    'name': '姓名',
    'dept_name': '院系名称',
    'course_name': '课程名称',
    'class_name': '班级名称',
    'major_name': '专业名称',
    'semester_name': '学期名称',
    'academic_year': '学年',
    'building': '宿舍楼',
    'room_number': '房间号',
    # 个人信息
    'gender': '性别',
    'birth_date': '出生日期',
    'id_card_no': '身份证号',
    'phone': '电话',
    'email': '邮箱',
    'address': '地址',
    'title': '职称',
    'dean': '院长',
    # 学生相关
    'enrollment_year': '入学年份',
    'status': '状态',
    'score': '成绩',
    'grade_point': '绩点',
    'grade_level': '等级',
    'min_score': '最低分',
    'max_score': '最高分',
    'description': '描述',
    # 课程相关
    'credits': '学分',
    'hours': '学时',
    'type': '类型',
    'classroom': '教室',
    'schedule': '时间安排',
    'capacity': '容量',
    # 专业相关
    'duration': '学制',
    'degree_type': '学位类型',
    'course_type': '课程类别',
    # 缴费相关
    'fee_type': '费用类型',
    'amount_due': '应缴金额',
    'amount_paid': '已缴金额',
    'payment_date': '缴费日期',
    'payment_method': '缴费方式',
    # 住宿相关
    'bed_number': '床位号',
    'check_in_date': '入住日期',
    'check_out_date': '退房日期',
    'occupied': '已住人数',
    'gender_limit': '性别限制',
    # 奖惩相关
    'rp_type': '奖惩类型',
    'level': '等级/级别',
    'date': '日期',
    'reason': '原因',
    'issuing_authority': '颁发机构',
    'operator': '操作人',
    'operator_ip': '操作IP',
    # 学期相关
    'start_date': '开始日期',
    'end_date': '结束日期',
    'is_current': '是否当前学期',
    # 时间戳
    'enroll_time': '选课时间',
    'created_at': '创建时间',
    'updated_at': '更新时间',
    'advisor': '辅导员',
    'remark': '备注',
    'semester': '学期',
}


# 关键字段列表：用于语义关联检测（跨表共享相同字段名即视为可关联）
KEY_FIELDS = [
    'student_id', 'dept_id', 'class_id', 'major_id', 'course_id',
    'teacher_id', 'semester_id', 'room_id', 'teaching_id',
    'academic_year', 'enrollment_year',
]

# 手动语义关联：为没有任何外键约束的表补充可关联关系
# key = 主表名, value = 关联列表 [{from_column, to_table, to_column}]
MANUAL_RELATIONS = {
    'classrooms': [
        {'from_column': 'classroom_name', 'to_table': 'teaching', 'to_column': 'classroom'},
    ],
}


class ComprehensiveQueryService:
    """综合查询服务"""

    def close(self):
        """兼容现有控制器调用模式（本服务无持久 session）"""
        pass

    def get_tables(self):
        """获取所有业务表列表，包含名称、标签、列数和列信息"""
        inspector = sa_inspect(engine)
        tables = []
        for table_name in inspector.get_table_names():
            if table_name not in TABLE_LABELS:
                continue
            columns = inspector.get_columns(table_name)
            col_info = []
            for col in columns:
                col_name = col['name']
                col_info.append({
                    'name': col_name,
                    'type': str(col['type']),
                    'label': FIELD_LABELS.get(col_name, col_name),
                })
            tables.append({
                'name': table_name,
                'label': TABLE_LABELS[table_name],
                'columns': col_info,
                'column_count': len(col_info),
            })
        return tables

    def get_table_fields(self, table_name):
        """获取指定表的所有字段信息"""
        inspector = sa_inspect(engine)
        columns = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = set(pk_constraint.get('constrained_columns', [])) if pk_constraint else set()
        fields = []
        for col in columns:
            col_name = col['name']
            fields.append({
                'name': col_name,
                'type': str(col['type']),
                'label': FIELD_LABELS.get(col_name, col_name),
                'is_pk': col_name in pk_columns,
            })
        return fields

    def get_table_relations(self, table_name):
        """获取指定表的关联关系（含双向FK + 语义关联）

        三种识别方式：
        1. 出站外键 — 当前表通过外键引用其他表
        2. 入站外键 — 其他表通过外键引用当前表
        3. 语义关联 — 基于共享关键字段名的跨表关联
        """
        inspector = sa_inspect(engine)
        relations = []
        from_label = TABLE_LABELS.get(table_name, table_name)
        seen_pairs = set()

        # ---- 1. 出站外键（当前表 → 其他表） ----
        fks = inspector.get_foreign_keys(table_name)
        for fk in fks:
            referred_table = fk['referred_table']
            if referred_table not in TABLE_LABELS:
                continue
            to_label = TABLE_LABELS[referred_table]
            constrained_cols = fk.get('constrained_columns', [])
            referred_cols = fk.get('referred_columns', [])
            for i, from_col in enumerate(constrained_cols):
                to_col = referred_cols[i] if i < len(referred_cols) else from_col
                pair = (table_name, referred_table, from_col, to_col)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    relations.append({
                        'from_table': table_name,
                        'from_label': from_label,
                        'from_column': from_col,
                        'to_table': referred_table,
                        'to_label': to_label,
                        'to_column': to_col,
                        'relation_type': 'foreign_key',
                    })

        # ---- 2. 入站外键（其他表 → 当前表） ----
        all_table_names = [t for t in TABLE_LABELS if t != table_name]
        for other_table in all_table_names:
            other_fks = inspector.get_foreign_keys(other_table)
            for fk in other_fks:
                if fk['referred_table'] != table_name:
                    continue
                constrained_cols = fk.get('constrained_columns', [])
                referred_cols = fk.get('referred_columns', [])
                for i, from_col in enumerate(constrained_cols):
                    to_col = referred_cols[i] if i < len(referred_cols) else from_col
                    pair = (table_name, other_table, to_col, from_col)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        relations.append({
                            'from_table': table_name,
                            'from_label': from_label,
                            'from_column': to_col,
                            'to_table': other_table,
                            'to_label': TABLE_LABELS.get(other_table, other_table),
                            'to_column': from_col,
                            'relation_type': 'reverse_foreign_key',
                        })

        # ---- 3. 语义关联（基于共享关键字段名） ----
        current_columns = {col['name'] for col in inspector.get_columns(table_name)}
        current_key_fields = [f for f in KEY_FIELDS if f in current_columns]

        if current_key_fields:
            for other_table in all_table_names:
                other_columns = {col['name'] for col in inspector.get_columns(other_table)}
                for key_field in current_key_fields:
                    if key_field not in other_columns:
                        continue
                    pair = (table_name, other_table, key_field, key_field)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        relations.append({
                            'from_table': table_name,
                            'from_label': from_label,
                            'from_column': key_field,
                            'to_table': other_table,
                            'to_label': TABLE_LABELS.get(other_table, other_table),
                            'to_column': key_field,
                            'relation_type': 'key_match',
                        })

        # ---- 4. 手动语义关联（为无FK的表补充关系） ----
        if table_name in MANUAL_RELATIONS:
            for manual_rel in MANUAL_RELATIONS[table_name]:
                to_table = manual_rel['to_table']
                if to_table not in TABLE_LABELS:
                    continue
                from_col = manual_rel['from_column']
                to_col = manual_rel['to_column']
                pair = (table_name, to_table, from_col, to_col)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    relations.append({
                        'from_table': table_name,
                        'from_label': from_label,
                        'from_column': from_col,
                        'to_table': to_table,
                        'to_label': TABLE_LABELS.get(to_table, to_table),
                        'to_column': to_col,
                        'relation_type': 'manual',
                    })

        return relations

    def execute_query(self, main_table, selected_joins, filters, page=1, page_size=20):
        """执行综合查询

        Args:
            main_table: 主表名
            selected_joins: JOIN 列表，每项为 {from_column, to_table, to_column}
            filters: 过滤条件列表，每项为 {field, op, value}，field 格式为 table.column
                     op 支持: =, !=, >, <, >=, <=, LIKE, IN
            page: 页码 (从 1 开始)
            page_size: 每页条数

        Returns:
            {ok, columns: [{key, label}], data: [...], total, page, total_pages}
        """
        session = SessionLocal()
        try:
            inspector = sa_inspect(engine)

            # ---- 构建所有相关表的列信息 ----
            table_aliases = {main_table: main_table}
            all_tables = [main_table]

            # 为 JOIN 表分配别名
            for join_info in selected_joins:
                tbl = join_info['to_table']
                if tbl not in table_aliases:
                    table_aliases[tbl] = tbl
                    all_tables.append(tbl)

            # 构建 SELECT 列：每列别名为 table_column
            select_cols = []
            columns_output = []
            for tbl in all_tables:
                alias = table_aliases[tbl]
                for col in inspector.get_columns(tbl):
                    col_name = col['name']
                    alias_name = f"{alias}_{col_name}"
                    select_cols.append(f'"{alias}"."{col_name}" AS "{alias_name}"')
                    columns_output.append({
                        'key': alias_name,
                        'label': FIELD_LABELS.get(col_name, col_name),
                        'table': tbl,
                        'table_label': TABLE_LABELS.get(tbl, tbl),
                    })

            # ---- 构建 FROM + LEFT JOIN 子句 ----
            from_clause = f'"{main_table}"'
            join_clauses = []
            for join_info in selected_joins:
                from_col = join_info['from_column']
                to_table = join_info['to_table']
                to_col = join_info['to_column']
                # from_col 格式为 table.column，to_table 在 join_info 中给出
                # 解析 from_column
                if '.' in from_col:
                    left_tbl, left_col = from_col.split('.', 1)
                else:
                    left_tbl = main_table
                    left_col = from_col
                join_clauses.append(
                    f'LEFT JOIN "{to_table}" ON "{left_tbl}"."{left_col}" = "{to_table}"."{to_col}"'
                )

            # ---- 构建 WHERE 子句 ----
            where_parts = []
            where_params = {}
            param_idx = 0

            SUPPORTED_OPS = {'=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN'}

            for f in filters:
                field = f.get('field', '')
                op = f.get('op', '=')
                value = f.get('value', '')

                if op not in SUPPORTED_OPS:
                    continue
                if not field:
                    continue

                # 解析 field 为 table.column
                if '.' in field:
                    tbl_name, col_name = field.split('.', 1)
                else:
                    tbl_name = main_table
                    col_name = field

                # 转义标识符，防止 SQL 注入
                param_name = f"p_{param_idx}"
                param_idx += 1

                if op.upper() == 'IN':
                    # value 应为逗号分隔的字符串
                    vals = [v.strip() for v in str(value).split(',') if v.strip()]
                    if not vals:
                        continue
                    placeholders = []
                    for vi, v in enumerate(vals):
                        pn = f"{param_name}_{vi}"
                        placeholders.append(f":{pn}")
                        where_params[pn] = v
                    where_parts.append(
                        f'"{tbl_name}"."{col_name}" IN ({", ".join(placeholders)})'
                    )
                elif op.upper() == 'LIKE':
                    # 转义 LIKE 值中的单引号和反斜杠
                    safe_value = str(value).replace('\\', '\\\\').replace("'", "''")
                    where_parts.append(
                        f'"{tbl_name}"."{col_name}" LIKE :{param_name}'
                    )
                    where_params[param_name] = safe_value
                else:
                    where_parts.append(
                        f'"{tbl_name}"."{col_name}" {op} :{param_name}'
                    )
                    where_params[param_name] = value

            where_clause = ''
            if where_parts:
                where_clause = 'WHERE ' + ' AND '.join(where_parts)

            # ---- 构建完整查询 ----
            sel = ', '.join(select_cols)
            joins = '\n'.join(join_clauses)

            # COUNT 查询
            count_sql = f"""
                SELECT COUNT(*) AS cnt
                FROM {from_clause}
                {joins}
                {where_clause}
            """
            count_result = session.execute(text(count_sql), where_params)
            total = count_result.scalar() or 0

            # 数据查询
            data_sql = f"""
                SELECT {sel}
                FROM {from_clause}
                {joins}
                {where_clause}
                ORDER BY 1
                LIMIT :_limit OFFSET :_offset
            """
            data_params = dict(where_params)
            data_params['_limit'] = page_size
            data_params['_offset'] = (page - 1) * page_size

            data_result = session.execute(text(data_sql), data_params)
            rows = []
            for row in data_result:
                row_dict = {}
                for col_meta in columns_output:
                    key = col_meta['key']
                    val = getattr(row, key, None)
                    # 转换不可 JSON 序列化的类型
                    if val is not None:
                        if hasattr(val, 'isoformat'):
                            val = val.isoformat()
                        elif isinstance(val, bytes):
                            val = val.decode('utf-8', errors='replace')
                    row_dict[key] = val
                rows.append(row_dict)

            total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

            return {
                'ok': True,
                'columns': columns_output,
                'data': rows,
                'total': total,
                'page': page,
                'total_pages': total_pages,
            }

        except Exception as e:
            session.rollback()
            return {
                'ok': False,
                'error': str(e),
                'columns': [],
                'data': [],
                'total': 0,
                'page': page,
                'total_pages': 1,
            }
        finally:
            session.close()
