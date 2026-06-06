"""
db_utils 模块单元测试
测试数据库连接获取、查询、增删改、分页查询等功能
"""

import sys
import os
import unittest

# 将项目根目录加入 sys.path，以便导入 student_system 下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import db_utils


def _check_db_available():
    """检查数据库是否可用，不可用则返回 None"""
    try:
        conn = db_utils.get_conn()
        conn.close()
        return True
    except Exception:
        return False


DB_AVAILABLE = _check_db_available()

# 测试数据标识前缀，便于清理
TEST_STUDENT_NO = 'TEST_001'
TEST_STUDENT_NO_2 = 'TEST_002'


@unittest.skipUnless(DB_AVAILABLE, '数据库不可用，跳过测试')
class TestDBUtils(unittest.TestCase):
    """db_utils 模块测试类"""

    def setUp(self):
        """每个测试前插入测试数据"""
        try:
            db_utils.execute(
                'INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name)'
                ' VALUES(%s,%s,%s,%s,%s,%s,%s)',
                (TEST_STUDENT_NO, '测试学生', '男', 20, '计算机', '2024', '计科1班')
            )
        except Exception:
            pass

    def tearDown(self):
        """每个测试后清理测试数据"""
        try:
            db_utils.execute(
                "DELETE FROM student_info WHERE student_no LIKE 'TEST_%'"
            )
        except Exception:
            pass

    def test_get_conn(self):
        """测试获取数据库连接是否成功"""
        conn = db_utils.get_conn()
        self.assertIsNotNone(conn)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                self.assertIsNotNone(result)
        finally:
            conn.close()

    def test_query(self):
        """测试查询功能：先插入测试数据，再查询验证"""
        rows = db_utils.query(
            'SELECT * FROM student_info WHERE student_no = %s',
            (TEST_STUDENT_NO,)
        )
        self.assertIsInstance(rows, list)
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]['student_no'], TEST_STUDENT_NO)
        self.assertEqual(rows[0]['student_name'], '测试学生')

    def test_execute(self):
        """测试增删改功能：插入→修改→删除完整流程"""
        # 插入
        rowcount = db_utils.execute(
            'INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name)'
            ' VALUES(%s,%s,%s,%s,%s,%s,%s)',
            (TEST_STUDENT_NO_2, '测试学生2', '女', 21, '软件工程', '2024', '软工1班')
        )
        self.assertEqual(rowcount, 1)

        # 验证插入
        rows = db_utils.query(
            'SELECT * FROM student_info WHERE student_no = %s',
            (TEST_STUDENT_NO_2,)
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['student_name'], '测试学生2')

        # 修改
        rowcount = db_utils.execute(
            'UPDATE student_info SET student_name=%s WHERE student_no=%s',
            ('修改后名字', TEST_STUDENT_NO_2)
        )
        self.assertEqual(rowcount, 1)

        # 验证修改
        rows = db_utils.query(
            'SELECT * FROM student_info WHERE student_no = %s',
            (TEST_STUDENT_NO_2,)
        )
        self.assertEqual(rows[0]['student_name'], '修改后名字')

        # 删除
        rowcount = db_utils.execute(
            'DELETE FROM student_info WHERE student_no = %s',
            (TEST_STUDENT_NO_2,)
        )
        self.assertEqual(rowcount, 1)

        # 验证删除
        rows = db_utils.query(
            'SELECT * FROM student_info WHERE student_no = %s',
            (TEST_STUDENT_NO_2,)
        )
        self.assertEqual(len(rows), 0)

    def test_get_page_data(self):
        """测试分页查询：验证返回结构包含 data/total/page/page_size/total_pages"""
        result = db_utils.get_page_data(
            'SELECT * FROM student_info WHERE student_no LIKE %s',
            page=1,
            page_size=10,
            params=('TEST_%',)
        )
        self.assertIn('data', result)
        self.assertIn('total', result)
        self.assertIn('page', result)
        self.assertIn('page_size', result)
        self.assertIn('total_pages', result)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['page_size'], 10)
        self.assertIsInstance(result['data'], list)
        self.assertIsInstance(result['total'], int)
        self.assertIsInstance(result['total_pages'], int)


if __name__ == '__main__':
    unittest.main()
