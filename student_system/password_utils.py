"""
密码安全工具模块
提供密码加盐哈希、验证等功能
"""
import hashlib
import secrets
import base64


def generate_salt(length=16):
    """
    生成随机盐值
    :param length: 盐值长度
    :return: 安全的随机盐值（base64编码）
    """
    salt = secrets.token_bytes(length)
    return base64.b64encode(salt).decode('utf-8')


def hash_password(password, salt=None):
    """
    使用盐值对密码进行哈希
    :param password: 原始密码
    :param salt: 可选的盐值，如果不提供则自动生成
    :return: (salt, hashed_password) 元组
    """
    if salt is None:
        salt = generate_salt()
    
    # 使用 SHA-256 进行哈希，盐值参与哈希计算
    password_bytes = password.encode('utf-8')
    salt_bytes = base64.b64decode(salt.encode('utf-8'))
    
    # 组合盐值和密码
    combined = salt_bytes + password_bytes
    
    # 多次迭代哈希，增加破解难度
    for _ in range(10000):
        hash_obj = hashlib.sha256(combined)
        combined = hash_obj.digest()
    
    hashed = base64.b64encode(combined).decode('utf-8')
    return salt, hashed


def encode_password_storage(salt, hashed_password):
    """
    将盐值和哈希后的密码组合成存储格式
    :param salt: 盐值
    :param hashed_password: 哈希后的密码
    :return: 存储用的字符串
    """
    return f"{salt}${hashed_password}"


def decode_password_storage(stored_password):
    """
    从存储格式中解析出盐值和哈希
    :param stored_password: 存储的密码字符串
    :return: (salt, hashed_password) 元组
    """
    if '$' not in stored_password:
        raise ValueError("Invalid password storage format")
    
    salt, hashed = stored_password.split('$', 1)
    return salt, hashed


def verify_password(password, stored_password):
    """
    验证密码是否正确
    :param password: 用户输入的密码
    :param stored_password: 存储的密码（盐值$哈希值 格式）
    :return: 是否匹配
    """
    salt, stored_hash = decode_password_storage(stored_password)
    
    # 使用相同的方法重新哈希
    _, computed_hash = hash_password(password, salt)
    
    # 使用安全的比较方法防止时序攻击
    return secrets.compare_digest(computed_hash, stored_hash)


def encrypt_password(password):
    """
    加密密码，返回用于存储的格式
    :param password: 原始密码
    :return: 存储格式的密码字符串
    """
    salt, hashed = hash_password(password)
    return encode_password_storage(salt, hashed)
