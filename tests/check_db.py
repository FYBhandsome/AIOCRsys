#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/visual_model")

from tortoise import Tortoise
from app.models.tortoise_models import User, Student
from config import settings

async def check():
    await Tortoise.init(db_url=settings.DATABASE_URL, modules={"models": ["app.models.tortoise_models"]})
    students = await Student.all()
    users = await User.all()
    print(f"Students: {len(students)}")
    for s in students:
        print(f"  - {s.id}: {s.name}")
    print(f"Users: {len(users)}")
    for u in users:
        print(f"  - {u.username}: {u.role}")
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check())
