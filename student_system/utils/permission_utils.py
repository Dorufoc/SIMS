"""
权限检查工具模块
提供用户权限验证、解析等功能
现在不直接依赖 Flask session，改为参数化
"""
import uuid


# 权限位定义
PERM_READ = 4    # 读权限
PERM_WRITE = 2   # 写权限
PERM_ADMIN = 1   # 管理权限


def generate_uuid():
    """生成 UUID v4"""
    return str(uuid.uuid4())


def parse_permission_code(code):
    """
    解析权限代码（如 '777'）为权限位
    返回 (read: bool, write: bool, admin: bool)
    
    权限代码格式（类似Linux权限）：
    - 4 = 读 (r)
    - 2 = 写 (w)  
    - 1 = 管理 (x)
    组合：7=读写管理, 6=读写, 4=只读, 2=只写, 0=无权限
    """
    if not code or len(code) < 1:
        return (False, False, False)
    
    # 取第一位数字
    try:
        perm = int(code[0])
    except ValueError:
        return (False, False, False)

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
