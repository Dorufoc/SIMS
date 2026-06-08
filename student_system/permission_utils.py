"""
权限检查工具模块
提供用户权限验证、解析等功能
"""
import uuid
from db_utils import query, execute
from functools import wraps
from flask import session, jsonify


# 权限位定义
PERM_READ = 4    # 读权限
PERM_WRITE = 2   # 写权限
PERM_ADMIN = 1   # 管理权限


def generate_uuid():
    """生成 UUID v4"""
    return str(uuid.uuid4())


def ensure_user_uuid(user_id):
    """确保用户有 UUID，如果没有则生成一个"""
    result = query("SELECT uuid FROM users WHERE user_id = %s", (user_id,))
    if not result or not result[0].get('uuid'):
        user_uuid = generate_uuid()
        execute("UPDATE users SET uuid = %s WHERE user_id = %s", (user_uuid, user_id))
        return user_uuid
    return result[0]['uuid']


def parse_permission_code(code):
    """
    解析权限代码（如 '777'）为权限位
    返回 (read: bool, write: bool, admin: bool)
    """
    if not code or len(code) < 1:
        return (False, False, False)
    
    # 取第一位数字
    perm = int(code[0])
    has_read = (perm & PERM_READ) == PERM_READ
    has_write = (perm & PERM_WRITE) == PERM_WRITE
    has_admin = (perm & PERM_ADMIN) == PERM_ADMIN
    
    return (has_read, has_write, has_admin)


def build_permission_code(can_read, can_write, can_admin):
    """
    根据权限位构建权限代码
    """
    perm = 0
    if can_read:
        perm |= PERM_READ
    if can_write:
        perm |= PERM_WRITE
    if can_admin:
        perm |= PERM_ADMIN
    return str(perm)


def get_user_permission(user_uuid, table_name):
    """
    获取用户对指定表的权限代码
    """
    result = query(
        "SELECT permission_code FROM user_permissions WHERE user_uuid = %s AND table_name = %s",
        (user_uuid, table_name)
    )
    if result:
        return result[0]['permission_code']
    return '000'


def set_user_permission(user_uuid, table_name, permission_code):
    """
    设置用户对指定表的权限
    """
    execute(
        """INSERT INTO user_permissions (user_uuid, table_name, permission_code) 
           VALUES (%s, %s, %s) 
           ON DUPLICATE KEY UPDATE permission_code = %s""",
        (user_uuid, table_name, permission_code, permission_code)
    )


def check_permission(user_id, table_name, required_perm):
    """
    检查用户是否有指定权限
    required_perm: PERM_READ, PERM_WRITE, or PERM_ADMIN
    """
    # 首先检查用户是否是超级管理员
    user_result = query("SELECT role FROM users WHERE user_id = %s", (user_id,))
    if user_result and user_result[0]['role'] == 'admin':
        return True
    
    # 获取用户 UUID
    user_uuid = ensure_user_uuid(user_id)
    
    # 获取权限
    perm_code = get_user_permission(user_uuid, table_name)
    has_read, has_write, has_admin = parse_permission_code(perm_code)
    
    if required_perm == PERM_READ:
        return has_read
    elif required_perm == PERM_WRITE:
        return has_write
    elif required_perm == PERM_ADMIN:
        return has_admin
    return False


def require_permission(table_name, required_perm):
    """
    权限检查装饰器
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'code': 1, 'msg': '请先登录'}), 401
            
            if not check_permission(session['user_id'], table_name, required_perm):
                return jsonify({'code': 1, 'msg': '权限不足'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin():
    """
    检查是否是超级管理员装饰器
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'code': 1, 'msg': '请先登录'}), 401
            
            user_result = query("SELECT role FROM users WHERE user_id = %s", (session['user_id'],))
            if not user_result or user_result[0]['role'] != 'admin':
                return jsonify({'code': 1, 'msg': '仅超级管理员可访问'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_user_permissions(user_uuid):
    """
    获取用户的所有权限
    """
    return query(
        "SELECT table_name, permission_code FROM user_permissions WHERE user_uuid = %s",
        (user_uuid,)
    )


def initialize_user_permissions(user_uuid, role='student'):
    """
    初始化新用户的权限，根据角色设置默认权限
    - student: 查看自己的信息、选课、成绩、培养计划、奖惩（可编辑联系方式）
    - teacher: 查看自己的信息、授课安排（可编辑联系方式）
    - admin: 统一无权限（通过角色绕过检查）
    """
    all_tables = [
        'departments', 'majors', 'classes', 'students', 'teachers', 'courses',
        'semesters', 'teaching', 'enrollments', 'grade_scale', 'rewards_punishments',
        'payments', 'dorm_rooms', 'dorm_assignments', 'curriculum', 'enroll_logs'
    ]

    if role == 'student':
        # 学生默认权限：只读查看与自己相关的数据，自己的信息可编辑
        perm_map = {
            'students': '600',              # 读+写（可修改联系方式）
            'enrollments': '400',           # 只读（选课和成绩）
            'courses': '400',               # 只读
            'curriculum': '400',            # 只读（培养计划）
            'rewards_punishments': '400',   # 只读（奖惩记录）
        }
    elif role == 'teacher':
        # 教师默认权限：只读查看与自己相关的数据，自己的信息可编辑
        perm_map = {
            'teachers': '600',              # 读+写（可修改联系方式）
            'teaching': '400',              # 只读（授课安排）
            'courses': '400',              # 只读
        }
    else:
        # admin 或其他角色：全部无权限（admin 通过角色绕过检查）
        perm_map = {}

    for table in all_tables:
        code = perm_map.get(table, '000')
        set_user_permission(user_uuid, table, code)
