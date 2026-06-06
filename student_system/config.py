"""
数据库连接配置及Flask应用密钥配置
从 db_config.xml 读取配置
"""

import os
import xml.etree.ElementTree as ET


def _load_config():
    """从 db_config.xml 加载配置"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_config.xml')
    tree = ET.parse(config_path)
    root = tree.getroot()

    db = root.find('database')
    flask = root.find('flask')

    return {
        'DB_HOST': db.findtext('host', ''),
        'DB_PORT': int(db.findtext('port', '3306')),
        'DB_USER': db.findtext('user', ''),
        'DB_PASSWORD': db.findtext('password', ''),
        'DB_NAME': db.findtext('name', ''),
        'SECRET_KEY': flask.findtext('secret_key', '') if flask is not None else '',
    }


_cfg = _load_config()

DB_HOST = _cfg['DB_HOST']
DB_PORT = _cfg['DB_PORT']
DB_USER = _cfg['DB_USER']
DB_PASSWORD = _cfg['DB_PASSWORD']
DB_NAME = _cfg['DB_NAME']
SECRET_KEY = _cfg['SECRET_KEY']
