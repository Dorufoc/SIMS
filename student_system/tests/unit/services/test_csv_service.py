# -*- coding: utf-8 -*-
"""Service 层测试 — CSV 服务"""
import os,sys
_pkg=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","__pypackages__")
if os.path.isdir(_pkg) and _pkg not in sys.path: sys.path.insert(0,_pkg)
import pytest
import io
from entity.base import Base, engine
from service.csv_service import CSVService
from entity.department import Department
from entity.major import Major
from entity.class_ import Class
from entity.student import Student

class TestCSVService:
    @pytest.fixture
    def svc(self):
        s = CSVService()
        yield s
        s.close()

    def test_generate_template(self, svc):
        output = svc.generate_template()
        content = output.read()
        assert "学号" in content
        assert "姓名" in content

    def test_parse_csv_valid(self, svc):
        csv_content = "学号,姓名,性别(M/F),入学年份\n2024001,张三,M,2024\n2024002,李四,F,2024\n"
        f = io.BytesIO(csv_content.encode("utf-8-sig"))
        result = svc.parse_csv(f)
        assert len(result["valid_data"]) == 2
        assert len(result["errors"]) == 0

    def test_parse_csv_empty_rows(self, svc):
        csv_content = "学号,姓名,性别(M/F),入学年份\n,张三,M,2024\n2024002,,F,2024\n"
        f = io.BytesIO(csv_content.encode("utf-8-sig"))
        result = svc.parse_csv(f)
        assert len(result["errors"]) >= 1

    def test_parse_csv_oversized(self, svc):
        csv_content = "学号,姓名,性别(M/F),入学年份\n" + "\n".join([f"2024{i:03d},学生{i},M,2024" for i in range(10001)])
        f = io.BytesIO(csv_content.encode("utf-8-sig"))
        result = svc.parse_csv(f)
        assert "超过限制" in result["errors"][0]

    def test_parse_csv_bad_headers(self, svc):
        csv_content = "id,name,gender\n1,test,M\n"
        f = io.BytesIO(csv_content.encode("utf-8-sig"))
        result = svc.parse_csv(f)
        assert "模板不正确" in result["errors"][0]

    def test_parse_csv_bad_enrollment_year(self, svc):
        csv_content = "学号,姓名,性别(M/F),入学年份\n2024001,张三,M,not_a_year\n"
        f = io.BytesIO(csv_content.encode("utf-8-sig"))
        result = svc.parse_csv(f)
        assert len(result["errors"]) >= 1

    def test_import_data(self, svc, reset_tables):
        count = svc.import_data([
            {"student_id": "CSV001", "name": "csv_test", "gender": "M", "enrollment_year": 2024}
        ])
        assert count == 1

    def test_import_data_update_existing(self, svc, reset_tables):
        svc.import_data([
            {"student_id": "CSV002", "name": "original", "gender": "M", "enrollment_year": 2024, "status": "在校"}
        ])
        count = svc.import_data([
            {"student_id": "CSV002", "name": "updated", "gender": "M", "enrollment_year": 2024, "status": "在校"}
        ])
        assert count == 0
        from entity.base import SessionLocal
        db = SessionLocal()
        stu = db.query(Student).filter(Student.student_id == "CSV002").first()
        assert stu.name == "updated"
        db.close()

    def test_export_csv(self, svc, reset_tables):
        svc.import_data([
            {"student_id": "CSV003", "name": "export_test", "gender": "F", "enrollment_year": 2024}
        ])
        output = svc.export_csv()
        content = output.read()
        assert "export_test" in content

    def test_export_csv_empty(self, svc, reset_tables):
        output = svc.export_csv()
        content = output.read()
        assert "学号" in content
