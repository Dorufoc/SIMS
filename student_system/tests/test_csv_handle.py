"""
csv_handle 模块单元测试
测试CSV模板生成、解析校验、导出等功能
"""

import sys
import os
import csv
from io import BytesIO, StringIO
import unittest
from unittest.mock import patch

# 将项目根目录加入 sys.path，以便导入 student_system 下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import csv_handle


class TestCSVHandle(unittest.TestCase):
    """csv_handle 模块测试类"""

    # ---- generate_template 测试 ----

    def test_generate_template(self):
        """测试模板生成：验证返回BytesIO、内容包含标准表头、无数据行"""
        result = csv_handle.generate_template()
        self.assertIsInstance(result, BytesIO)

        content = result.read().decode('utf-8-sig')
        reader = csv.reader(StringIO(content))
        rows = list(reader)

        # 包含标准表头
        self.assertEqual(rows[0], csv_handle.HEADERS)
        # 无数据行（只有表头一行）
        self.assertEqual(len(rows), 1)

    # ---- parse_csv 测试 ----

    def _make_csv_stream(self, rows):
        """辅助方法：将行列表构建为 CSV BytesIO 流"""
        output = StringIO()
        writer = csv.writer(output)
        for row in rows:
            writer.writerow(row)
        byte_output = BytesIO()
        byte_output.write(output.getvalue().encode('utf-8-sig'))
        byte_output.seek(0)
        return byte_output

    @patch('csv_handle.db_utils.query', return_value=[])
    def test_parse_csv_valid(self, mock_query):
        """测试解析合法CSV：验证返回valid_data列表和空errors"""
        stream = self._make_csv_stream([
            csv_handle.HEADERS,
            ['TEST_1001', '张三', '男', '20', '计算机', '2024', '计科1班'],
        ])
        result = csv_handle.parse_csv(stream)
        self.assertIsInstance(result['valid_data'], list)
        self.assertEqual(len(result['valid_data']), 1)
        self.assertEqual(result['valid_data'][0][0], 'TEST_1001')
        self.assertEqual(result['errors'], [])

    @patch('csv_handle.db_utils.query', return_value=[])
    def test_parse_csv_empty_student_no(self, mock_query):
        """测试学号为空的行被标记异常"""
        stream = self._make_csv_stream([
            csv_handle.HEADERS,
            ['', '张三', '男', '20', '计算机', '2024', '计科1班'],
        ])
        result = csv_handle.parse_csv(stream)
        self.assertEqual(len(result['valid_data']), 0)
        self.assertTrue(any('学号为空' in e for e in result['errors']))

    @patch('csv_handle.db_utils.query', return_value=[])
    def test_parse_csv_invalid_age(self, mock_query):
        """测试年龄非数字的行被标记异常"""
        stream = self._make_csv_stream([
            csv_handle.HEADERS,
            ['TEST_1002', '李四', '女', 'abc', '软件工程', '2024', '软工1班'],
        ])
        result = csv_handle.parse_csv(stream)
        self.assertEqual(len(result['valid_data']), 0)
        self.assertTrue(any('年龄非数字' in e for e in result['errors']))

    @patch('csv_handle.db_utils.query', return_value=[])
    def test_parse_csv_skip_header(self, mock_query):
        """测试表头行被跳过"""
        stream = self._make_csv_stream([
            csv_handle.HEADERS,
            ['TEST_1003', '王五', '男', '22', '自动化', '2024', '自控1班'],
        ])
        result = csv_handle.parse_csv(stream)
        # 表头行不应出现在 valid_data 中
        self.assertEqual(len(result['valid_data']), 1)
        self.assertEqual(result['valid_data'][0][0], 'TEST_1003')

    @patch('csv_handle.db_utils.query', return_value=[])
    def test_parse_csv_skip_empty_row(self, mock_query):
        """测试空行被跳过"""
        stream = self._make_csv_stream([
            csv_handle.HEADERS,
            [],
            ['TEST_1004', '赵六', '男', '19', '自动化', '2024', '自控2班'],
            ['', '', '', '', '', '', ''],
        ])
        result = csv_handle.parse_csv(stream)
        self.assertEqual(len(result['valid_data']), 1)
        self.assertEqual(result['valid_data'][0][0], 'TEST_1004')

    @patch('csv_handle.db_utils.query', return_value=[])
    def test_parse_csv_duplicate_student_no(self, mock_query):
        """测试学号重复被标记异常"""
        stream = self._make_csv_stream([
            csv_handle.HEADERS,
            ['TEST_1005', '甲', '男', '20', '计算机', '2024', '计科1班'],
            ['TEST_1005', '乙', '女', '21', '计算机', '2024', '计科2班'],
        ])
        result = csv_handle.parse_csv(stream)
        # 第一条合法，第二条因学号重复被标记
        self.assertEqual(len(result['valid_data']), 1)
        self.assertTrue(any('重复' in e for e in result['errors']))

    # ---- export_csv 测试 ----

    @patch('csv_handle.db_utils.query')
    def test_export_csv(self, mock_query):
        """测试导出功能：验证返回BytesIO、包含BOM头、包含标准表头"""
        mock_query.return_value = [
            {
                'student_no': 'TEST_2001',
                'student_name': '导出测试',
                'gender': '男',
                'age': 20,
                'major': '计算机',
                'grade': '2024',
                'class_name': '计科1班',
            }
        ]
        result = csv_handle.export_csv()
        self.assertIsInstance(result, BytesIO)

        raw = result.read()
        # 验证包含 BOM 头
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))

        # 解码并验证表头（使用 utf-8-sig 去除 BOM）
        content = raw.decode('utf-8-sig')
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        self.assertEqual(rows[0], csv_handle.HEADERS)
        self.assertGreaterEqual(len(rows), 2)


if __name__ == '__main__':
    unittest.main()
