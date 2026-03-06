#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准备测试数据
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config import settings

async def prepare_test_data():
    """准备测试数据"""
    print("初始化数据库...")
    
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models"]}
    )
    await Tortoise.generate_schemas()
    
    from app.models.tortoise_models import Student, User
    from app.core.security import get_password_hash
    
    print("检查测试用户...")
    
    admin_user = await User.get_or_none(username="admin")
    if not admin_user:
        await User.create(
            username="admin",
            password=get_password_hash("admin123"),
            role="admin",
            email="admin@test.com",
            real_name="系统管理员",
            is_active=True
        )
        print("创建管理员用户: admin")
    
    teacher_user = await User.get_or_none(username="teacher")
    if not teacher_user:
        await User.create(
            username="teacher",
            password=get_password_hash("teacher123"),
            role="teacher",
            email="teacher@test.com",
            real_name="测试教师",
            is_active=True
        )
        print("创建教师用户: teacher")
    
    student_user = await User.get_or_none(username="student_202300502128")
    if not student_user:
        await User.create(
            username="student_202300502128",
            password=get_password_hash("student123"),
            role="student",
            email="student@test.com",
            real_name="测试学生",
            student_id="202300502128",
            is_active=True
        )
        print("创建学生用户: student_202300502128")
    
    print("检查测试学生...")
    
    test_student = await Student.get_or_none(id="202300502101")
    if not test_student:
        await Student.create(
            id="202300502101",
            name="张三",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        print("创建测试学生: 202300502101")
    
    test_student2 = await Student.get_or_none(id="202300502128")
    if not test_student2:
        await Student.create(
            id="202300502128",
            name="测试学生",
            college="计算机学院",
            major="计算机科学与技术",
            class_name="计算机2301",
            grade="2023"
        )
        print("创建测试学生: 202300502128")
    
    print("测试数据准备完成!")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(prepare_test_data())
