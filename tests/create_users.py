#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/visual_model")

from tortoise import Tortoise
from app.models.tortoise_models import User
from app.core.security import get_password_hash
from config import settings

async def create_users():
    await Tortoise.init(db_url=settings.DATABASE_URL, modules={"models": ["app.models.tortoise_models"]})
    
    test_users = [
        {"username": "admin", "password": "admin123", "role": "admin", "email": "admin@test.com", "real_name": "管理员"},
        {"username": "teacher", "password": "teacher123", "role": "teacher", "email": "teacher@test.com", "real_name": "测试教师"},
        {"username": "student_202300502128", "password": "student123", "role": "student", "email": "student@test.com", "real_name": "樊意彬", "student_id": "202300502128"},
    ]
    
    for user_data in test_users:
        existing = await User.filter(username=user_data["username"]).first()
        if existing:
            print(f"用户已存在: {user_data['username']}")
            continue
        
        await User.create(
            username=user_data["username"],
            password=get_password_hash(user_data["password"]),
            role=user_data["role"],
            email=user_data["email"],
            real_name=user_data["real_name"],
            student_id=user_data.get("student_id"),
            is_active=True
        )
        print(f"创建用户: {user_data['username']} ({user_data['role']})")
    
    await Tortoise.close_connections()
    print("完成!")

if __name__ == "__main__":
    asyncio.run(create_users())
