"""
密码安全工具模块
提供 bcrypt 密码哈希、验证等功能，兼容旧版 SHA-256 格式
"""
import hashlib
import secrets
import base64
import bcrypt


# ==================== 旧格式兼容函数（内部使用） ====================

def generate_salt(length=16):
    """
    生成随机盐值（旧 SHA-256 格式兼容用）
    :param length: 盐值长度
    :return: 安全的随机盐值（base64编码）
    """
    salt = secrets.token_bytes(length)
    return base64.b64encode(salt).decode('utf-8')


def hash_password(password, salt=None):
    """
    使用盐值对密码进行 SHA-256 哈希（旧格式兼容用）
    :param password: 原始密码
    :param salt: 可选的盐值，如果不提供则自动生成
    :return: (salt, hashed_password) 元组
    """
    if salt is None:
        salt = generate_salt()

    password_bytes = password.encode('utf-8')
    salt_bytes = base64.b64decode(salt.encode('utf-8'))

    combined = salt_bytes + password_bytes

    for _ in range(10000):
        hash_obj = hashlib.sha256(combined)
        combined = hash_obj.digest()

    hashed = base64.b64encode(combined).decode('utf-8')
    return salt, hashed


def encode_password_storage(salt, hashed_password):
    """
    将盐值和哈希后的密码组合成旧版存储格式
    :param salt: 盐值
    :param hashed_password: 哈希后的密码
    :return: 存储用的字符串（salt$hash 格式）
    """
    return f"{salt}${hashed_password}"


def decode_password_storage(stored_password):
    """
    从旧版存储格式中解析出盐值和哈希
    :param stored_password: 存储的密码字符串
    :return: (salt, hashed_password) 元组
    """
    if '$' not in stored_password:
        raise ValueError("Invalid password storage format")

    salt, hashed = stored_password.split('$', 1)
    return salt, hashed


# ==================== bcrypt 主接口 ====================

def encrypt_password(password):
    """
    使用 bcrypt 哈希密码
    :param password: 原始密码
    :return: bcrypt 哈希字符串（自带盐值）
    """
    password_bytes = password.encode('utf-8')
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')


def verify_password(password, stored_password):
    """
    验证密码是否正确，兼容旧版 SHA-256 格式。
    旧格式密码验证通过后会自动提供 bcrypt 升级哈希。

    :param password: 用户输入的密码
    :param stored_password: 存储的密码（bcrypt 格式或旧版 salt$hash 格式）
    :return: (is_valid: bool, needs_upgrade: bool, upgraded_hash: Optional[str])
    """
    # bcrypt 格式：以 $2b$ 或 $2a$ 开头
    if stored_password.startswith('$2b$') or stored_password.startswith('$2a$'):
        password_bytes = password.encode('utf-8')
        stored_bytes = stored_password.encode('utf-8')
        is_valid = bcrypt.checkpw(password_bytes, stored_bytes)
        return is_valid, False, None

    # 旧版 SHA-256 格式：salt$hashed_password
    try:
        salt, stored_hash = decode_password_storage(stored_password)
    except ValueError:
        return False, False, None

    _, computed_hash = hash_password(password, salt)
    is_valid = secrets.compare_digest(computed_hash, stored_hash)

    if is_valid:
        upgraded_hash = encrypt_password(password)
        return True, True, upgraded_hash

    return False, False, None
