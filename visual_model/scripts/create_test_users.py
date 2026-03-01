#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试用户脚本
"""
import sqlite3
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash

DB_PATH = "D:/PaddleOCR/visual_model/data/database.db"

def create_test_users():
    """创建测试用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("创建测试用户...")
    
    test_users = [
        {
            "username": "admin",
            "password": get_password_hash("admin123"),
            "email": "admin@test.com",
            "phone": "系统管理员",
            "student_id": None,
            "teacher_id": None,
            "role": "admin",
            "status": "active"
        },
        {
            "username": "teacher",
            "password": get_password_hash("teacher123"),
            "email": "teacher_new@test.com",
            "phone": "测试教师",
            "student_id": None,
            "teacher_id": "T001",
            "role": "teacher",
            "status": "active"
        },
        {
            "username": "student_202300502128",
            "password": get_password_hash("student123"),
            "email": "student_202300502128@test.com",
            "phone": "测试学生",
            "student_id": "202300502128",
            "teacher_id": None,
            "role": "student",
            "status": "active"
        }
    ]
    
    for user in test_users:
        try:
            cursor.execute("SELECT id FROM users WHERE username = ?", (user["username"],))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE users SET 
                        password_hash = ?,
                        email = ?,
                        phone = ?,
                        student_id = ?,
                        teacher_id = ?,
                        role = ?,
                        status = ?
                    WHERE username = ?
                """, (
                    user["password"],
                    user["email"],
                    user["phone"],
                    user["student_id"],
                    user["teacher_id"],
                    user["role"],
                    user["status"],
                    user["username"]
                ))
                print(f"  更新用户: {user['username']}")
            else:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, phone, student_id, teacher_id, role, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user["username"],
                    user["password"],
                    user["email"],
                    user["phone"],
                    user["student_id"],
                    user["teacher_id"],
                    user["role"],
                    user["status"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                print(f"  创建用户: {user['username']}")
        except Exception as e:
            print(f"  处理用户 {user['username']} 失败: {e}")
    
    conn.commit()
    conn.close()
    print("测试用户创建完成!")

if __name__ == "__main__":
    create_test_users()
