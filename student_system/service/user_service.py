"""用户管理服务"""
from repository.user_repo import UserRepo
from repository.user_permission_repo import UserPermissionRepo
from repository.base import escape_like
from utils.password_utils import encrypt_password
from utils.permission_utils import generate_uuid, init_user_permissions


class UserService:
    def __init__(self):
        self.user_repo = UserRepo()
        self.perm_repo = UserPermissionRepo()

    def close(self):
        self.user_repo.close()
        self.perm_repo.close()

    def get_list(self, page=1, page_size=10, filters=None, keyword=None):
        """获取用户列表"""
        from entity.user import User
        q = self.user_repo.db.query(
            User.user_id, User.uuid, User.username, User.role,
            User.ref_id, User.last_login, User.created_at
        )

        if keyword:
            escaped = escape_like(keyword)
            q = q.filter(
                (User.username.like(f'%{escaped}%', escape='\\')) |
                (User.ref_id.like(f'%{escaped}%', escape='\\'))
            )

        q = q.order_by(User.created_at.desc())
        return self.user_repo.paginate(page, page_size, q)

    def create(self, data: dict):
        """创建用户"""
        from entity.user import User
        password = data.get('password')
        if not password:
            return False, '密码不能为空'
        role = data.get('role', 'student')
        if role not in ['admin', 'teacher', 'student']:
            role = 'student'

        try:
            user_uuid = generate_uuid()
            user = User(
                uuid=user_uuid,
                username=data['username'],
                password_hash=encrypt_password(password),
                role=role,
                ref_id=data.get('ref_id') or None,
            )
            self.user_repo.create(user)

            # 初始化权限
            init_user_permissions(self.perm_repo, user_uuid, role)
            return True, '创建成功'
        except Exception:
            self.user_repo.db.rollback()
            return False, '创建失败（用户名可能已存在）'

    def update(self, user_id: int, data: dict):
        """更新用户"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, '用户不存在'

        if 'username' in data and data['username']:
            user.username = data['username']
        if 'role' in data and data['role'] in ['admin', 'teacher', 'student']:
            user.role = data['role']
        if 'ref_id' in data:
            user.ref_id = data['ref_id']
        if 'password' in data and data['password']:
            user.password_hash = encrypt_password(data['password'])

        self.user_repo.db.commit()
        return True, '更新成功'

    def delete(self, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        self.perm_repo.delete_by_user_uuid(user.uuid)
        return self.user_repo.delete_by_id(user_id)

    def get_permissions(self, user_id: int):
        """获取用户权限"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return []
        return self.perm_repo.find_by_user_uuid(user.uuid)

    def set_permissions(self, user_id: int, permissions: list):
        """设置用户权限"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, '用户不存在'

        for perm in permissions:
            table_name = perm.get('table_name', '')
            perm_code = perm.get('permission_code', '000')
            self.perm_repo.upsert(user.uuid, table_name, perm_code)

        return True, '权限设置成功'

    def get_tables(self):
        """获取所有表名"""
        tables = [
            {'name': 'departments', 'label': '院系表'},
            {'name': 'majors', 'label': '专业表'},
            {'name': 'classes', 'label': '班级表'},
            {'name': 'students', 'label': '学生表'},
            {'name': 'teachers', 'label': '教师表'},
            {'name': 'courses', 'label': '课程表'},
            {'name': 'semesters', 'label': '学期表'},
            {'name': 'teaching', 'label': '授课安排表'},
            {'name': 'enrollments', 'label': '选课表'},
            {'name': 'rewards_punishments', 'label': '奖惩表'},
            {'name': 'payments', 'label': '缴费表'},
            {'name': 'dorm_rooms', 'label': '宿舍表'},
            {'name': 'dorm_assignments', 'label': '住宿分配表'},
        ]
        return tables

