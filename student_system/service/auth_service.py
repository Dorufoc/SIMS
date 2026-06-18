"""认证服务"""
import re
from repository.user_repo import UserRepo
from repository.user_permission_repo import UserPermissionRepo
from utils.password_utils import encrypt_password, verify_password
from utils.permission_utils import generate_uuid, init_user_permissions


# 离线模式默认管理员凭据
_OFFLINE_ADMIN = {
    'username': 'admin',
    'password': 'admin',
}


class AuthService:
    def __init__(self):
        self.user_repo = UserRepo()
        self.perm_repo = UserPermissionRepo()

    def close(self):
        self.user_repo.close()
        self.perm_repo.close()

    @staticmethod
    def local_login(identifier: str, password: str):
        """离线模式本地登录校验（不依赖数据库）
        
        仅在数据库不可用时作为降级方案。
        """
        if identifier == _OFFLINE_ADMIN['username'] and password == _OFFLINE_ADMIN['password']:
            return True, '登录成功（离线模式）', {
                'user_id': 0,
                'username': 'admin',
                'role': 'admin',
                'ref_id': None,
                'uuid': '00000000-0000-0000-0000-000000000001',
                'need_set_username': False,
                'username_changed': True,
            }
        return False, '账号或密码错误', None

    def login(self, identifier: str, password: str):
        """用户登录，返回 (success, message, user_dict_or_none)"""
        user = self.user_repo.find_by_identifier(identifier)
        if not user:
            return False, '账号或密码错误', None

        is_valid, needs_upgrade, upgraded_hash = verify_password(password, user.password_hash)
        if not is_valid:
            return False, '账号或密码错误', None

        # 旧格式密码自动升级为 bcrypt
        if needs_upgrade and upgraded_hash:
            user.password_hash = upgraded_hash

        # 登录时自动关联：若用户有 ref_id，补齐人员信息
        if user.ref_id and user.role == 'student':
            from entity.student import Student
            person = self.user_repo.db.query(Student).filter(
                Student.student_id == user.ref_id
            ).first()
            if person and not user.real_name and person.name:
                user.real_name = person.name
        elif user.ref_id and user.role == 'teacher':
            from entity.teacher import Teacher
            person = self.user_repo.db.query(Teacher).filter(
                Teacher.teacher_id == user.ref_id
            ).first()
            if person and not user.real_name and person.name:
                user.real_name = person.name

        # 更新最后登录时间
        from datetime import datetime
        user.last_login = datetime.now()
        self.user_repo.db.commit()

        # 非管理员且未完成用户名修改时，需要强制修改用户名
        need_set_username = False
        if user.role != 'admin' and not user.username_changed:
            need_set_username = True

        return True, '登录成功', {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'ref_id': user.ref_id,
            'uuid': user.uuid,
            'need_set_username': need_set_username,
            'username_changed': user.username_changed,
        }

    def register(self, password: str, real_name: str, role: str,
                 register_method: str, register_value: str):
        """用户注册，返回 (success, message, user_dict_or_none)"""
        if role not in ['admin', 'teacher', 'student']:
            role = 'student'

        if register_method != 'ref_id':
            return False, '请选择有效的注册方式', None

        if not register_value:
            return False, '请输入注册信息', None

        if not password or len(password) < 6:
            return False, '密码长度不能少于6位', None

        # 检查是否已被注册
        existing = self.user_repo.find_by(ref_id=register_value)
        if existing:
            return False, '该编号已被注册', None

        # 根据角色在对应库中做前置校验
        from entity.student import Student
        from entity.teacher import Teacher

        person = None
        if role == 'student':
            person = self.user_repo.db.query(Student).filter(
                Student.student_id == register_value
            ).first()
        elif role == 'teacher':
            person = self.user_repo.db.query(Teacher).filter(
                Teacher.teacher_id == register_value
            ).first()

        if not person:
            return False, '未在该角色库中找到该编号，请核对后重试；如确认无误请联系管理员补充基础信息', None

        try:
            user_uuid = generate_uuid()
            temp_username = 'tmp_' + user_uuid[:8]
            encrypted = encrypt_password(password)

            user_data = {
                'uuid': user_uuid,
                'username': temp_username,
                'password_hash': encrypted,
                'role': role,
                'real_name': real_name or '',
                'username_changed': False,
                'ref_id': register_value,
            }
            user = self.user_repo.create(self.user_repo.model(**user_data))

            # 直接设置关联信息
            if role == 'student':
                user.ref_id = person.student_id
                user.real_name = person.name
            elif role == 'teacher':
                user.ref_id = person.teacher_id
                user.real_name = person.name

            self.user_repo.db.commit()

            # 初始化权限
            init_user_permissions(self.perm_repo, user_uuid, role)

            # 返回完整用户信息供自动登录
            return True, '注册成功', {
                'user_id': user.user_id,
                'username': user.username,
                'role': user.role,
                'ref_id': user.ref_id,
                'uuid': user.uuid,
                'need_set_username': True,
                'username_changed': False,
            }
        except Exception as e:
            self.user_repo.db.rollback()
            return False, '注册失败，请稍后重试', None

    def set_username(self, user_id, new_username):
        """设置/修改用户名"""
        if not new_username:
            return False, '用户名不能为空', None
        if len(new_username) < 3 or len(new_username) > 50:
            return False, '用户名长度需在3-50个字符之间', None
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', new_username):
            return False, '用户名只能包含字母、数字、下划线和中文', None

        # 检查重复
        existing = self.user_repo.find_by_username(new_username)
        if existing and existing.user_id != user_id:
            return False, '该用户名已被使用', None

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, '用户不存在', None
        user.username = new_username
        user.username_changed = True
        self.user_repo.db.commit()
        return True, '用户名设置成功', new_username

    @staticmethod
    def _validate_password_strength(password: str):
        """校验密码强度，返回 (is_valid, message)"""
        if len(password) < 8:
            return False, '密码长度不能少于8位'
        if not re.search(r'[A-Z]', password):
            return False, '密码需包含至少一个大写字母'
        if not re.search(r'[a-z]', password):
            return False, '密码需包含至少一个小写字母'
        if not re.search(r'\d', password):
            return False, '密码需包含至少一个数字'
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\\/\-_=+`~]', password):
            return False, '密码需包含至少一个特殊字符'
        return True, ''

    def change_password(self, user_id, old_password, new_password):
        """修改密码"""
        if not old_password:
            return False, '请输入旧密码'
        if not new_password:
            return False, '请输入新密码'

        is_strong, msg = self._validate_password_strength(new_password)
        if not is_strong:
            return False, msg

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, '用户不存在'

        is_valid, needs_upgrade, upgraded_hash = verify_password(old_password, user.password_hash)
        if not is_valid:
            return False, '旧密码错误'

        user.password_hash = encrypt_password(new_password)
        self.user_repo.db.commit()
        return True, '密码修改成功'

