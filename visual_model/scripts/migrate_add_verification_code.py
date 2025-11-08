#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加验证码相关字段

为用户表添加：
- verification_code: 验证码
- code_expires_at: 验证码过期时间
"""

import sqlite3
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.logger import logger


def migrate_database(db_path: str = None):
    """执行数据库迁移
    
    Args:
        db_path: 数据库文件路径，默认使用配置文件中的路径
    """
    if not db_path:
        db_path = PROJECT_ROOT / "data" / "database.db"
    
    logger.info(f"开始迁移数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        changes_made = False
        
        # 添加 verification_code 字段
        if 'verification_code' not in columns:
            logger.info("添加 verification_code 字段...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN verification_code VARCHAR(10)
            """)
            changes_made = True
            logger.info("✓ verification_code 字段添加成功")
        else:
            logger.info("verification_code 字段已存在，跳过")
        
        # 添加 code_expires_at 字段
        if 'code_expires_at' not in columns:
            logger.info("添加 code_expires_at 字段...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN code_expires_at TIMESTAMP
            """)
            changes_made = True
            logger.info("✓ code_expires_at 字段添加成功")
        else:
            logger.info("code_expires_at 字段已存在，跳过")
        
        if changes_made:
            conn.commit()
            logger.info("✓ 数据库迁移完成！")
        else:
            logger.info("✓ 数据库已是最新版本，无需迁移")
        
        # 显示更新后的表结构
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        logger.info("\n当前用户表结构：")
        for col in columns_info:
            logger.info(f"  - {col[1]}: {col[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移：添加验证码字段")
    print("=" * 60)
    
    # 检查是否提供了自定义数据库路径
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = migrate_database(db_path)
    
    if success:
        print("\n✓ 迁移成功完成！")
        sys.exit(0)
    else:
        print("\n✗ 迁移失败，请检查日志")
        sys.exit(1)

