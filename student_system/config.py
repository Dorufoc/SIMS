"""
应用配置模块 - 从环境变量读取
"""
import os
from dotenv import load_dotenv

load_dotenv()

FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# SECRET_KEY 校验：生产环境必须从环境变量设置
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if FLASK_ENV == 'production':
        raise RuntimeError('SECRET_KEY 环境变量未设置，生产环境必须提供 SECRET_KEY')
    SECRET_KEY = 'dev-secret-key'

# DATABASE_URL 校验：生产环境不允许硬编码回退值
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    if FLASK_ENV == 'production':
        raise RuntimeError('DATABASE_URL 环境变量未设置，生产环境必须提供 DATABASE_URL')
    DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/student_manage'

# 上传限制：最大 10MB
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
