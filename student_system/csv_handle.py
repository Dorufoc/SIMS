"""
CSV文件处理模块，提供模板生成、解析、导入、导出功能
"""

import csv
from io import BytesIO, StringIO

import db_utils

# 标准表头定义
HEADERS = ['学号', '姓名', '性别', '年龄', '专业', '年级', '班级']

# 数据库字段与表头对应顺序
FIELD_ORDER = [
    'student_no', 'student_name', 'gender',
    'age', 'major', 'grade', 'class_name'
]


def generate_template():
    """在内存生成标准表头CSV模板（无数据行），返回BytesIO对象"""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    byte_output = BytesIO()
    byte_output.write(output.getvalue().encode('utf-8-sig'))
    byte_output.seek(0)
    return byte_output


def parse_csv(file_stream):
    """解析上传的CSV文件，校验数据合法性，返回合法数据与错误信息"""
    content = file_stream.read().decode('utf-8-sig')
    reader = csv.reader(StringIO(content))

    rows = list(reader)

    valid_data = []
    errors = []
    seen_student_no = set()

    for index, row in enumerate(rows):
        # 跳过表头行（第一行）
        if index == 0:
            continue

        # 空行自动跳过
        if not row or all(cell.strip() == '' for cell in row):
            continue

        # 补齐不足7列的行
        while len(row) < 7:
            row.append('')

        row = [cell.strip() for cell in row[:7]]
        student_no, student_name, gender, age, major, grade, class_name = row
        row_num = index + 1  # 显示用行号（从1开始）

        # 校验：学号为空
        if not student_no:
            errors.append(f"第{row_num}行: 学号为空")
            continue

        # 校验：年龄非数字
        if age and not age.isdigit():
            errors.append(f"第{row_num}行: 年龄非数字")
            continue

        # 校验：学号重复（先检查本文件内重复）
        if student_no in seen_student_no:
            errors.append(f"第{row_num}行: 学号{student_no}在文件中重复")
            continue
        seen_student_no.add(student_no)

        # 校验：学号在数据库中已存在
        existing = db_utils.query(
            "SELECT student_no FROM student_info WHERE student_no = %s",
            (student_no,)
        )
        if existing:
            errors.append(f"第{row_num}行: 学号{student_no}已存在")
            continue

        # 合法数据
        age_val = int(age) if age else None
        valid_data.append([student_no, student_name, gender, age_val, major, grade, class_name])

    return {
        'valid_data': valid_data,
        'errors': errors
    }


def import_data(valid_data):
    """批量导入数据，使用事务保证一致性，返回成功条数"""
    conn = None
    cursor = None
    try:
        conn = db_utils.get_conn()
        cursor = conn.cursor()
        cursor.execute("BEGIN")

        insert_sql = (
            "INSERT INTO student_info"
            "(student_no,student_name,gender,age,major,grade,class_name)"
            " VALUES(%s,%s,%s,%s,%s,%s,%s)"
        )

        for row in valid_data:
            cursor.execute(insert_sql, row)

        conn.commit()
        return len(valid_data)
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def export_csv(query_sql=None, params=None):
    """根据查询条件导出CSV数据，返回BytesIO对象（含BOM头）"""
    if query_sql is None:
        query_sql = "SELECT student_no,student_name,gender,age,major,grade,class_name FROM student_info"

    rows = db_utils.query(query_sql, params)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(HEADERS)

    for row in rows:
        writer.writerow([row.get(field, '') for field in FIELD_ORDER])

    byte_output = BytesIO()
    byte_output.write('\ufeff'.encode('utf-8'))
    byte_output.write(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    return byte_output
