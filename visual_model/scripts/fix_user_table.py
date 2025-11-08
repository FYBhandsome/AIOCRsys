#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复users表的schema - 将student_id改为可NULL
此脚本用于修复数据库schema问题，允许教师和管理员注册（他们没有student_id）
"""
import sqlite3
import sys
from pathlib import Path

def fix_users_table():
    """重建users表，使student_id字段可以为NULL"""
    # 获取数据库路径（相对于脚本位置）
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'data' / 'database.db'
    
    if not db_path.exists():
        print(f"错误: 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始修复users表...")
        print(f"数据库路径: {db_path}")
        
        # 1. 创建新表（student_id为NULL）
        print("\n  [1/4] 创建临时表...")
        cursor.execute("""
            CREATE TABLE "users_new" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                "username" VARCHAR(50) UNIQUE,
                "email" VARCHAR(255) UNIQUE,
                "password" VARCHAR(255) NOT NULL,
                "role" VARCHAR(20) NOT NULL DEFAULT 'student',
                "student_id" VARCHAR(50) UNIQUE,
                "real_name" VARCHAR(100),
                "class_id" VARCHAR(50),
                "is_active" INTEGER NOT NULL DEFAULT 1,
                "is_email_verified" INTEGER NOT NULL DEFAULT 0,
                "reset_token" VARCHAR(255),
                "reset_token_expires" TIMESTAMP,
                "last_login" TIMESTAMP,
                "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                "extra_info" JSON
            )
        """)
        print("      临时表创建成功")
        
        # 2. 复制数据（如果有）
        print("\n  [2/4] 复制现有数据...")
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("""
                INSERT INTO users_new 
                (id, username, email, password, role, student_id, real_name, class_id,
                 is_active, is_email_verified, reset_token, reset_token_expires,
                 last_login, created_at, updated_at, extra_info)
                SELECT 
                 id, username, email, password, role, student_id, real_name, class_id,
                 is_active, is_email_verified, reset_token, reset_token_expires,
                 last_login, created_at, updated_at, extra_info
                FROM users
            """)
            print(f"      已复制 {count} 条记录")
        else:
            print("      表中没有数据，跳过复制")
        
        # 3. 删除旧表
        print("\n  [3/4] 删除旧表...")
        cursor.execute("DROP TABLE users")
        print("      旧表已删除")
        
        # 4. 重命名新表
        print("\n  [4/4] 重命名新表...")
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        print("      新表已重命名为users")
        
        # 提交更改
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ users表修复成功！")
        print("=" * 60)
        print("\n修复内容:")
        print("  • student_id字段现在可以为NULL")
        print("  • 教师和管理员可以正常注册")
        print(f"  • 保留了原有 {count} 条用户记录")
        
        # 验证新表结构
        print("\n新表结构:")
        print("-" * 60)
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        schema = cursor.fetchone()[0]
        print(schema)
        print("-" * 60)
        
        conn.close()
        
        print("\n提示: 请重启后端服务以使更改生效")
        print("      python visual_model/main.py")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  数据库Schema修复工具")
    print("  Database Schema Fix Tool")
    print("=" * 60)
    print()
    
    success = fix_users_table()
    sys.exit(0 if success else 1)

