#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试开发人员账号脚本
创建具有全部功能访问权限的测试账号
"""
import asyncio
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.models.tortoise_models import User
from app.core.security import get_password_hash
from config import settings


async def create_test_accounts():
    """创建测试账号"""
    print("=" * 60)
    print("创建测试开发人员账号")
    print("=" * 60)
    
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models"]}
    )
    await Tortoise.generate_schemas()
    
    test_accounts = [
        {
            "username": "dev_admin",
            "password": "dev123456",
            "role": "admin",
            "email": "dev_admin@test.com",
            "real_name": "开发管理员",
            "description": "测试开发人员 - 完全访问权限"
        },
        {
            "username": "dev_teacher",
            "password": "dev123456",
            "role": "teacher",
            "email": "dev_teacher@test.com",
            "real_name": "开发教师",
            "description": "测试开发人员 - 教师权限"
        },
        {
            "username": "dev_student",
            "password": "dev123456",
            "role": "student",
            "email": "dev_student@test.com",
            "real_name": "开发学生",
            "description": "测试开发人员 - 学生权限"
        },
        {
            "username": "admin",
            "password": "admin123",
            "role": "admin",
            "email": "admin@test.com",
            "real_name": "系统管理员",
            "description": "系统管理员账号"
        },
        {
            "username": "teacher",
            "password": "teacher123",
            "role": "teacher",
            "email": "teacher@test.com",
            "real_name": "测试教师",
            "description": "教师测试账号"
        },
        {
            "username": "student_202300502128",
            "password": "student123",
            "role": "student",
            "email": "student@test.com",
            "real_name": "测试学生",
            "student_id": "202300502128",
            "description": "学生测试账号"
        }
    ]
    
    created_count = 0
    existing_count = 0
    
    for account in test_accounts:
        existing = await User.filter(username=account["username"]).first()
        if existing:
            print(f"  ⚠️ 用户已存在: {account['username']} ({account['role']})")
            existing_count += 1
            continue
        
        await User.create(
            username=account["username"],
            password=get_password_hash(account["password"]),
            role=account["role"],
            email=account["email"],
            real_name=account["real_name"],
            student_id=account.get("student_id"),
            is_active=True,
            is_email_verified=True
        )
        print(f"  ✓ 创建用户: {account['username']} ({account['role']}) - {account['description']}")
        created_count += 1
    
    await Tortoise.close_connections()
    
    print("\n" + "=" * 60)
    print(f"完成! 创建: {created_count}, 已存在: {existing_count}")
    print("=" * 60)
    print("\n测试账号列表:")
    print("-" * 60)
    print("| 用户名              | 密码       | 角色     | 说明           |")
    print("-" * 60)
    print("| dev_admin           | dev123456  | admin    | 开发管理员     |")
    print("| dev_teacher         | dev123456  | teacher  | 开发教师       |")
    print("| dev_student         | dev123456  | student  | 开发学生       |")
    print("| admin               | admin123   | admin    | 系统管理员     |")
    print("| teacher             | teacher123 | teacher  | 测试教师       |")
    print("| student_202300502128| student123 | student  | 测试学生       |")
    print("-" * 60)


if __name__ == "__main__":
    asyncio.run(create_test_accounts())
