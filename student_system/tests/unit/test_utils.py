# -*- coding: utf-8 -*-
"""Utils 单元测试 — password_utils + permission_utils"""
import os
import sys
_pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '__pypackages__')
if os.path.isdir(_pkg) and _pkg not in sys.path:
    sys.path.insert(0, _pkg)

import pytest
import base64
from utils.password_utils import (
    encrypt_password, verify_password, hash_password,
    generate_salt, encode_password_storage, decode_password_storage
)
from utils.permission_utils import (
    parse_permission_code, build_permission_code, generate_uuid,
    PERM_READ, PERM_WRITE, PERM_ADMIN
)


# ========== password_utils ==========

class TestEncryptPassword:
    def test_encrypt_password_returns_bcrypt(self):
        """加密密码返回值应为非空字符串，且包含分隔符"""
        h = encrypt_password('test123456')
        assert isinstance(h, str) and len(h) > 10
        assert '$' in h

    def test_encrypt_password_different_each_time(self):
        h1 = encrypt_password('samepass')
        h2 = encrypt_password('samepass')
        assert h1 != h2


class TestVerifyPassword:
    def test_verify_bcrypt_correct(self):
        import bcrypt
        print('DEBUG bcrypt location:', bcrypt.__file__)
        h = encrypt_password('mypassword')
        print('DEBUG hash:', repr(h), 'starts $2b$:', h.startswith('$2b$'), 'starts $2a$:', h.startswith('$2a$'))
        valid, needs_upgrade, upgraded = verify_password('mypassword', h)
        print('DEBUG result:', valid, needs_upgrade, upgraded)
        assert valid is True
        assert needs_upgrade is False
        assert upgraded is None

    def test_verify_bcrypt_wrong(self):
        h = encrypt_password('correctpass')
        valid, needs_upgrade, upgraded = verify_password('wrongpass', h)
        assert valid is False
        assert needs_upgrade is False

    def test_verify_sha256_legacy(self):
        salt, hashed = hash_password('oldpassword')
        stored = encode_password_storage(salt, hashed)
        valid, needs_upgrade, upgraded = verify_password('oldpassword', stored)
        assert valid is True
        assert needs_upgrade is True
        assert upgraded is not None and isinstance(upgraded, str)
        assert len(upgraded) > 10
        assert upgraded != stored

    def test_verify_sha256_wrong_password(self):
        salt, hashed = hash_password('realpass')
        stored = encode_password_storage(salt, hashed)
        valid, needs_upgrade, upgraded = verify_password('wrongpass', stored)
        assert valid is False
        assert needs_upgrade is False

    def test_verify_invalid_format(self):
        valid, needs_upgrade, upgraded = verify_password('any', 'not-a-valid-format')
        assert valid is False
        assert needs_upgrade is False
        assert upgraded is None


class TestHashPassword:
    def test_hash_password_without_salt(self):
        salt, hashed = hash_password('mypassword')
        assert salt is not None
        assert hashed is not None

    def test_hash_password_with_salt(self):
        salt = base64.b64encode(os.urandom(16)).decode('utf-8')
        _, h1 = hash_password('test', salt)
        _, h2 = hash_password('test', salt)
        assert h1 == h2

    def test_hash_password_different_salt_different_hash(self):
        _, h1 = hash_password('test')
        _, h2 = hash_password('test')
        assert h1 != h2


class TestGenerateSalt:
    def test_generate_salt_default_length(self):
        salt = generate_salt()
        decoded = base64.b64decode(salt.encode('utf-8'))
        assert len(decoded) == 16

    def test_generate_salt_unique(self):
        s1 = generate_salt()
        s2 = generate_salt()
        assert s1 != s2


class TestEncodeDecodePasswordStorage:
    def test_encode_decode_roundtrip(self):
        salt = 'test_salt_value'
        hashed = 'test_hashed_value'
        stored = encode_password_storage(salt, hashed)
        decoded_salt, decoded_hashed = decode_password_storage(stored)
        assert decoded_salt == salt
        assert decoded_hashed == hashed

    def test_decode_invalid_format(self):
        with pytest.raises(ValueError, match='Invalid password storage format'):
            decode_password_storage('no_dollar_sign')


# ========== permission_utils ==========

class TestParsePermissionCode:
    def test_777(self):
        r, w, a = parse_permission_code('777')
        assert r is True and w is True and a is True

    def test_600(self):
        r, w, a = parse_permission_code('600')
        assert r is True and w is True and a is False

    def test_400(self):
        r, w, a = parse_permission_code('400')
        assert r is True and w is False and a is False

    def test_200(self):
        r, w, a = parse_permission_code('200')
        assert r is False and w is True and a is False

    def test_100(self):
        r, w, a = parse_permission_code('100')
        assert r is False and w is False and a is True

    def test_000(self):
        r, w, a = parse_permission_code('000')
        assert r is False and w is False and a is False

    def test_empty_code(self):
        r, w, a = parse_permission_code('')
        assert r is False and w is False and a is False

    def test_invalid_code(self):
        r, w, a = parse_permission_code('abc')
        assert r is False and w is False and a is False

    def test_perm_constants(self):
        assert PERM_READ == 4
        assert PERM_WRITE == 2
        assert PERM_ADMIN == 1


class TestBuildPermissionCode:
    def test_all_true(self):
        assert build_permission_code(True, True, True) == '7'

    def test_read_write(self):
        assert build_permission_code(True, True, False) == '6'

    def test_read_only(self):
        assert build_permission_code(True, False, False) == '4'

    def test_none(self):
        assert build_permission_code(False, False, False) == '0'


class TestGenerateUUID:
    def test_uuid_format(self):
        u = generate_uuid()
        parts = u.split('-')
        assert len(parts) == 5

    def test_uuid_unique(self):
        u1 = generate_uuid()
        u2 = generate_uuid()
        assert u1 != u2
