#!/usr/bin/env python
"""
密码加密系统测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import password_utils


def test_password_system():
    """
    测试密码加密和验证系统
    """
    print("=" * 60)
    print("密码加密系统测试")
    print("=" * 60)
    
    test_cases = [
        "admin123",
        "password123",
        "test123",
        "mypassword",
        "a" * 20,
    ]
    
    print("\n1. 密码加密测试")
    print("-" * 40)
    for password in test_cases:
        encrypted = password_utils.encrypt_password(password)
        print(f"  原始: {password}")
        print(f"  加密: {encrypted}")
        print()
    
    print("\n2. 密码验证测试")
    print("-" * 40)
    all_passed = True
    for password in test_cases:
        encrypted = password_utils.encrypt_password(password)
        
        # 测试正确密码
        result = password_utils.verify_password(password, encrypted)
        print(f"  ✓ 密码 '{password}' 验证: {'成功' if result else '失败'}")
        if not result:
            all_passed = False
        
        # 测试错误密码
        wrong_password = password + "wrong"
        result = password_utils.verify_password(wrong_password, encrypted)
        print(f"  ✗ 密码 '{wrong_password}' 验证: {'成功' if result else '失败'} (预期失败)")
        if result:
            all_passed = False
        print()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败!")
    print("=" * 60)


if __name__ == "__main__":
    test_password_system()
