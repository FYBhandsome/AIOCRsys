#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据初始化脚本
创建测试用户、班级、学生等数据
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config import settings
from app.models.tortoise_models import User, Class, Student, ComprehensiveScore, ComprehensiveScoreConfig, ScoreDetail
from app.core.security import get_password_hash


TEST_USERS = [
    {
        "username": "test_admin",
        "password": "admin123456",
        "role": "admin",
        "email": "admin@test.com",
        "real_name": "测试管理员",
        "is_active": True
    },
    {
        "username": "test_teacher",
        "password": "teacher123456",
        "role": "teacher",
        "email": "teacher@test.com",
        "real_name": "测试教师",
        "is_active": True
    },
    {
        "username": "test_student_001",
        "password": "student123456",
        "role": "student",
        "email": "student001@test.com",
        "real_name": "张三",
        "student_id": "202300502001",
        "is_active": True
    },
    {
        "username": "test_student_002",
        "password": "student123456",
        "role": "student",
        "email": "student002@test.com",
        "real_name": "李四",
        "student_id": "202300502002",
        "is_active": True
    },
    {
        "username": "test_student_003",
        "password": "student123456",
        "role": "student",
        "email": "student003@test.com",
        "real_name": "王五",
        "student_id": "202300502003",
        "is_active": True
    }
]

TEST_CLASSES = [
    {
        "id": "test_class_001",
        "name": "测试班级2301",
        "grade": "2023",
        "major": "计算机科学与技术",
        "college": "计算机学院",
        "student_count": 2
    },
    {
        "id": "test_class_002",
        "name": "测试班级2302",
        "grade": "2023",
        "major": "软件工程",
        "college": "计算机学院",
        "student_count": 1
    }
]

TEST_STUDENTS = [
    {
        "id": "202300502001",
        "name": "张三",
        "gender": "男",
        "class_name": "测试班级2301",
        "major": "计算机科学与技术",
        "grade": "2023"
    },
    {
        "id": "202300502002",
        "name": "李四",
        "gender": "女",
        "class_name": "测试班级2301",
        "major": "计算机科学与技术",
        "grade": "2023"
    },
    {
        "id": "202300502003",
        "name": "王五",
        "gender": "男",
        "class_name": "测试班级2302",
        "major": "软件工程",
        "grade": "2023"
    }
]

TEST_CONFIGS = [
    {
        "name": "默认综测配置",
        "description": "系统默认的综合测评配置",
        "a_weight": 20.0,
        "b_weight": 70.0,
        "c_weight": 10.0,
        "academic_score_field": "weighted_average",
        "academic_score_scale": 1.0,
        "is_default": True,
        "is_active": True
    }
]


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models", "aerich.models"]}
    )
    await Tortoise.generate_schemas()
    print("✓ 数据库连接初始化完成")


async def create_test_users():
    """创建测试用户"""
    print("\n创建测试用户...")
    created_count = 0
    
    for user_data in TEST_USERS:
        existing = await User.filter(username=user_data["username"]).first()
        if existing:
            print(f"  - 用户 {user_data['username']} 已存在，跳过")
            continue
        
        password = user_data.pop("password")
        user = await User.create(
            **user_data,
            password=get_password_hash(password)
        )
        created_count += 1
        print(f"  ✓ 创建用户: {user.username} (角色: {user.role})")
    
    print(f"共创建 {created_count} 个用户")


async def create_test_classes():
    """创建测试班级"""
    print("\n创建测试班级...")
    created_count = 0
    
    for class_data in TEST_CLASSES:
        existing = await Class.filter(id=class_data["id"]).first()
        if existing:
            print(f"  - 班级 {class_data['name']} 已存在，跳过")
            continue
        
        cls = await Class.create(**class_data)
        created_count += 1
        print(f"  ✓ 创建班级: {cls.name}")
    
    print(f"共创建 {created_count} 个班级")


async def create_test_students():
    """创建测试学生"""
    print("\n创建测试学生...")
    created_count = 0
    
    for student_data in TEST_STUDENTS:
        existing = await Student.filter(id=student_data["id"]).first()
        if existing:
            print(f"  - 学生 {student_data['name']} 已存在，跳过")
            continue
        
        student = await Student.create(**student_data)
        created_count += 1
        print(f"  ✓ 创建学生: {student.name} ({student.id})")
    
    print(f"共创建 {created_count} 个学生")


async def create_test_configs():
    """创建测试配置"""
    print("\n创建综测配置...")
    created_count = 0
    
    for config_data in TEST_CONFIGS:
        existing = await ComprehensiveScoreConfig.filter(name=config_data["name"]).first()
        if existing:
            print(f"  - 配置 {config_data['name']} 已存在，跳过")
            continue
        
        config = await ComprehensiveScoreConfig.create(**config_data)
        created_count += 1
        print(f"  ✓ 创建配置: {config.name}")
    
    print(f"共创建 {created_count} 个配置")


async def create_test_scores():
    """创建测试成绩数据"""
    print("\n创建测试成绩数据...")
    
    student = await Student.filter(id="202300502001").first()
    if not student:
        print("  - 未找到测试学生，跳过成绩创建")
        return
    
    existing = await ComprehensiveScore.filter(
        student_id=student.id,
        academic_year="2023-2024",
        semester="1"
    ).first()
    
    if existing:
        print("  - 成绩数据已存在，跳过")
        return
    
    score = await ComprehensiveScore.create(
        student_id=student.id,
        academic_year="2023-2024",
        semester="1",
        a1_score=100.0,
        a2_score=10.0,
        a3_score=0.0,
        a_total_score=22.0,
        b_total_score=70.0,
        c1_score=8.0,
        c2_score=0.0,
        c3_score=0.0,
        c4_score=0.0,
        c_total_score=0.8,
        total_score=92.8
    )
    print(f"  ✓ 创建成绩记录: {score.total_score}分")
    
    details = [
        {
            "student_id": student.id,
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "A2",
            "item_name": "优秀学生干部",
            "score": 5.0,
            "description": "担任班长"
        },
        {
            "student_id": student.id,
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "C1",
            "item_name": "蓝桥杯省赛一等奖",
            "score": 8.0,
            "description": "省级学科竞赛"
        }
    ]
    
    for detail_data in details:
        await ScoreDetail.create(**detail_data)
    
    print(f"  ✓ 创建 {len(details)} 条成绩明细")


async def main():
    """主函数"""
    print("=" * 60)
    print("综测计算助手 - 测试数据初始化")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await init_db()
        await create_test_users()
        await create_test_classes()
        await create_test_students()
        await create_test_configs()
        await create_test_scores()
        
        print("\n" + "=" * 60)
        print("✓ 测试数据初始化完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
