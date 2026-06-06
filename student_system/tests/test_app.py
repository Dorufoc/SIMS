"""
app 模块路由集成测试
测试用户认证、学生CRUD、CSV导入导出、角色权限等功能
"""

import sys
import os
import unittest

# 将项目根目录加入 sys.path，以便导入 student_system 下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import app as flask_app
import db_utils


def _check_db_available():
    """检查数据库是否可用"""
    try:
        conn = db_utils.get_conn()
        conn.close()
        return True
    except Exception:
        return False


DB_AVAILABLE = _check_db_available()

# 测试数据标识
TEST_USER = 'TEST_USER_001'
TEST_PASSWORD = 'test123'
TEST_ADMIN = 'TEST_ADMIN_001'
TEST_ADMIN_PASSWORD = 'admin123'
TEST_STUDENT_NO = 'TEST_S001'
TEST_STUDENT_NO_2 = 'TEST_S002'


@unittest.skipUnless(DB_AVAILABLE, '数据库不可用，跳过测试')
class TestAuth(unittest.TestCase):
    """用户认证路由测试类"""

    @classmethod
    def setUpClass(cls):
        """注册测试用户"""
        try:
            db_utils.execute(
                'INSERT INTO user_info(username,password,real_name,role) VALUES(%s,%s,%s,%s)',
                (TEST_USER, TEST_PASSWORD, '测试用户', 'user')
            )
        except Exception:
            pass
        try:
            db_utils.execute(
                'INSERT INTO user_info(username,password,real_name,role) VALUES(%s,%s,%s,%s)',
                (TEST_ADMIN, TEST_ADMIN_PASSWORD, '测试管理员', 'admin')
            )
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        """清理测试用户"""
        try:
            db_utils.execute(
                "DELETE FROM user_info WHERE username LIKE 'TEST_%'"
            )
        except Exception:
            pass

    def setUp(self):
        self.app = flask_app.app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_register_success(self):
        """注册成功"""
        unique_user = f'TEST_REG_{os.getpid()}'
        resp = self.client.post('/register', data={
            'username': unique_user,
            'password': 'test123',
            'real_name': '注册测试',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 0)
        # 清理
        db_utils.execute("DELETE FROM user_info WHERE username = %s", (unique_user,))

    def test_register_duplicate(self):
        """用户名重复注册"""
        resp = self.client.post('/register', data={
            'username': TEST_USER,
            'password': 'test123',
            'real_name': '重复用户',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 1)

    def test_login_success(self):
        """登录成功"""
        resp = self.client.post('/login', data={
            'username': TEST_USER,
            'password': TEST_PASSWORD,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 0)

    def test_login_fail(self):
        """登录失败"""
        resp = self.client.post('/login', data={
            'username': TEST_USER,
            'password': 'wrong_password',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 1)

    def test_logout(self):
        """退出登录"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = TEST_USER
            sess['user_role'] = 'user'
        resp = self.client.get('/logout')
        # 退出后应重定向到登录页
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers.get('Location', ''))

    def test_auth_required(self):
        """未登录访问受保护路由重定向到登录页"""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers.get('Location', ''))


@unittest.skipUnless(DB_AVAILABLE, '数据库不可用，跳过测试')
class TestStudentCRUD(unittest.TestCase):
    """学生CRUD路由测试类"""

    def setUp(self):
        self.app = flask_app.app
        self.app.testing = True
        self.client = self.app.test_client()
        # 以管理员身份登录
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = TEST_ADMIN
            sess['user_role'] = 'admin'
        # 清理可能残留的测试数据
        try:
            db_utils.execute("DELETE FROM student_info WHERE student_no LIKE 'TEST_%'")
        except Exception:
            pass

    def tearDown(self):
        try:
            db_utils.execute("DELETE FROM student_info WHERE student_no LIKE 'TEST_%'")
        except Exception:
            pass

    def test_add_student(self):
        """新增学生成功"""
        resp = self.client.post('/add', data={
            'student_no': TEST_STUDENT_NO,
            'student_name': '测试学生',
            'gender': '男',
            'age': '20',
            'major': '计算机',
            'grade': '2024',
            'class_name': '计科1班',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 0)

    def test_add_duplicate_student_no(self):
        """学号重复"""
        # 先插入一条
        db_utils.execute(
            'INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name)'
            ' VALUES(%s,%s,%s,%s,%s,%s,%s)',
            (TEST_STUDENT_NO, '已有学生', '男', 20, '计算机', '2024', '计科1班')
        )
        # 再用相同学号新增
        resp = self.client.post('/add', data={
            'student_no': TEST_STUDENT_NO,
            'student_name': '重复学生',
            'gender': '女',
            'age': '21',
            'major': '软件工程',
            'grade': '2024',
            'class_name': '软工1班',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 1)

    def test_manage_page(self):
        """访问管理页面"""
        resp = self.client.get('/manage')
        self.assertEqual(resp.status_code, 200)

    def test_edit_student(self):
        """编辑学生"""
        # 先插入测试数据
        db_utils.execute(
            'INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name)'
            ' VALUES(%s,%s,%s,%s,%s,%s,%s)',
            (TEST_STUDENT_NO, '编辑前', '男', 20, '计算机', '2024', '计科1班')
        )
        rows = db_utils.query(
            'SELECT id FROM student_info WHERE student_no = %s',
            (TEST_STUDENT_NO,)
        )
        student_id = rows[0]['id']

        # 编辑
        resp = self.client.post(f'/edit/{student_id}', data={
            'student_name': '编辑后',
            'gender': '女',
            'age': '21',
            'major': '软件工程',
            'grade': '2024',
            'class_name': '软工1班',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 0)

        # 验证修改结果
        rows = db_utils.query(
            'SELECT student_name FROM student_info WHERE id = %s',
            (student_id,)
        )
        self.assertEqual(rows[0]['student_name'], '编辑后')

    def test_delete_student(self):
        """删除学生"""
        # 先插入测试数据
        db_utils.execute(
            'INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name)'
            ' VALUES(%s,%s,%s,%s,%s,%s,%s)',
            (TEST_STUDENT_NO, '待删除', '男', 20, '计算机', '2024', '计科1班')
        )
        rows = db_utils.query(
            'SELECT id FROM student_info WHERE student_no = %s',
            (TEST_STUDENT_NO,)
        )
        student_id = rows[0]['id']

        # 删除
        resp = self.client.post(f'/delete/{student_id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 0)

        # 验证已删除
        rows = db_utils.query(
            'SELECT * FROM student_info WHERE id = %s',
            (student_id,)
        )
        self.assertEqual(len(rows), 0)


@unittest.skipUnless(DB_AVAILABLE, '数据库不可用，跳过测试')
class TestCSV(unittest.TestCase):
    """CSV导入导出路由测试类"""

    def setUp(self):
        self.app = flask_app.app
        self.app.testing = True
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = TEST_ADMIN
            sess['user_role'] = 'admin'

    def test_csv_template_download(self):
        """下载模板"""
        resp = self.client.get('/csv/template')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp.content_type)

    def test_csv_export(self):
        """全量导出"""
        resp = self.client.get('/csv/export')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp.content_type)


@unittest.skipUnless(DB_AVAILABLE, '数据库不可用，跳过测试')
class TestRolePermission(unittest.TestCase):
    """角色权限路由测试类"""

    def setUp(self):
        self.app = flask_app.app
        self.app.testing = True
        self.client = self.app.test_client()
        # 清理可能残留的测试数据
        try:
            db_utils.execute("DELETE FROM student_info WHERE student_no LIKE 'TEST_%'")
        except Exception:
            pass

    def tearDown(self):
        try:
            db_utils.execute("DELETE FROM student_info WHERE student_no LIKE 'TEST_%'")
        except Exception:
            pass

    def test_admin_can_add(self):
        """管理员可以新增"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = TEST_ADMIN
            sess['user_role'] = 'admin'

        resp = self.client.post('/add', data={
            'student_no': TEST_STUDENT_NO,
            'student_name': '管理员新增',
            'gender': '男',
            'age': '20',
            'major': '计算机',
            'grade': '2024',
            'class_name': '计科1班',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 0)

    def test_user_cannot_add(self):
        """只读用户不能新增（返回权限不足）"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['user_name'] = TEST_USER
            sess['user_role'] = 'user'

        resp = self.client.post('/add', data={
            'student_no': TEST_STUDENT_NO_2,
            'student_name': '普通用户新增',
            'gender': '女',
            'age': '21',
            'major': '软件工程',
            'grade': '2024',
            'class_name': '软工1班',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['code'], 2)
        self.assertIn('权限不足', data['msg'])


if __name__ == '__main__':
    unittest.main()
