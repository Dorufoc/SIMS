"""CSV 导入导出服务"""
import csv
import io
from datetime import date
from repository.student_repo import StudentRepo
from entity.student import Student


class CSVService:
    def __init__(self):
        self.repo = StudentRepo()

    def close(self):
        self.repo.close()

    def generate_template(self):
        """生成 CSV 模板"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            '学号', '姓名', '性别(M/F)', '出生日期(YYYY-MM-DD)', '身份证号',
            '入学年份', '班级编号', '手机号', '邮箱', '地址'
        ])
        writer.writerow([
            '2024001', '张三', 'M', '2000-01-01', '110101200001011234',
            '2024', '1', '13800138000', 'zhangsan@example.com', '北京市'
        ])
        output.seek(0)
        return output

    def parse_csv(self, file_stream):
        """解析 CSV 文件并校验"""
        valid_data = []
        errors = []
        content = file_stream.read().decode('utf-8-sig')

        # 安全检查：限制行数
        lines = content.split('\n')
        if len(lines) > 10000:
            return {'valid_data': [], 'errors': ['文件行数超过限制（最多 10000 行）']}

        reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames or '学号' not in reader.fieldnames:
            return {'valid_data': [], 'errors': ['CSV 模板不正确，请使用标准模板']}

        for i, row in enumerate(reader, start=2):
            student_id = row.get('学号', '').strip()
            name = row.get('姓名', '').strip()
            if not student_id or not name:
                errors.append(f'第{i}行：学号或姓名不能为空')
                continue
            try:
                enrollment_year = int(row.get('入学年份', '').strip() or date.today().year)
            except (ValueError, TypeError):
                errors.append(f'第{i}行：入学年份格式不正确')
                continue

            try:
                class_id_raw = row.get('班级编号', '').strip()
                class_id = int(class_id_raw) if class_id_raw else None
            except (ValueError, TypeError):
                class_id = None

            valid_data.append({
                'student_id': student_id,
                'name': name,
                'gender': row.get('性别(M/F)', '').strip() or 'M',
                'birth_date': row.get('出生日期(YYYY-MM-DD)', '').strip() or None,
                'id_card_no': row.get('身份证号', '').strip() or None,
                'enrollment_year': enrollment_year,
                'class_id': class_id,
                'phone': row.get('手机号', '').strip() or None,
                'email': row.get('邮箱', '').strip() or None,
                'address': row.get('地址', '').strip() or None,
                'status': '在校',
            })

        return {'valid_data': valid_data, 'errors': errors}

    def import_data(self, valid_data: list):
        """批量导入学生数据"""
        count = 0
        for item in valid_data:
            existing = self.repo.find_by_student_id(item['student_id'])
            if existing:
                for k, v in item.items():
                    if hasattr(existing, k) and v is not None:
                        setattr(existing, k, v)
            else:
                student = Student(**item)
                self.repo.db.add(student)
                count += 1
        self.repo.db.commit()
        return count

    def export_csv(self, query_results=None):
        """导出 CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            '学号', '姓名', '性别', '出生日期', '身份证号',
            '入学年份', '状态', '手机号', '邮箱', '地址'
        ])

        students = query_results if query_results is not None else self.repo.get_all()
        for s in students:
            writer.writerow([
                s.student_id, s.name,
                '男' if s.gender == 'M' else ('女' if s.gender == 'F' else ''),
                str(s.birth_date) if s.birth_date else '',
                s.id_card_no or '', s.enrollment_year, s.status or '在校',
                s.phone or '', s.email or '', s.address or ''
            ])

        output.seek(0)
        return output
