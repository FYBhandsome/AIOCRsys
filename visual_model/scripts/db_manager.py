#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据库管理和迁移脚本
集成了数据库初始化、迁移、备份、恢复等所有功能

使用方法：
    python db_manager.py init              # 初始化数据库
    python db_manager.py check             # 检查数据库表
    python db_manager.py migrate           # 执行数据库迁移
    python db_manager.py migrate-users     # 修复users表schema
    python db_manager.py migrate-academic  # 创建academic_scores表
    python db_manager.py migrate-config    # 创建综测配置表
    python db_manager.py backup            # 备份数据库
    python db_manager.py reset             # 重置数据库
    python db_manager.py sample            # 创建示例数据
"""

import asyncio
import argparse
import sys
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.core.logger import logger
from app.core.db_connection import get_db_connection_manager
from app.models.tortoise_models import (
    User, Student, AcademicScore, ComprehensiveScore, 
    ComprehensiveScoreConfig, File
)
from app.services.database_tortoise import DatabaseService
from config import settings


class DatabaseManager:
    """统一数据库管理器"""
    
    def __init__(self):
        self.db_manager = get_db_connection_manager()
        self.db_service = DatabaseService()
        self.db_path = Path(settings.DATABASE_PATH)
    
    async def init_connection(self):
        """初始化数据库连接"""
        return await self.db_manager.init_connection()
    
    async def close_connection(self):
        """关闭数据库连接"""
        await self.db_manager.close_connection()
    
    async def create_tables(self):
        """创建数据库表"""
        try:
            from tortoise import Tortoise
            # 生成数据库表结构（safe=True 表示如果表已存在则跳过）
            await Tortoise.generate_schemas(safe=True)
            logger.info("数据库表创建/更新成功")
            return True
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}", exc_info=True)
            return False
    
    async def check_tables(self):
        """检查数据库表是否存在"""
        try:
            conn = Tortoise.get_connection("default")
            tables = await conn.execute_query_dict(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            
            logger.info("当前数据库表:")
            for table in tables:
                table_name = table['name']
                if not table_name.startswith('sqlite_'):
                    # 获取记录数
                    count_result = await conn.execute_query_dict(
                        f"SELECT COUNT(*) as count FROM {table_name}"
                    )
                    count = count_result[0]['count'] if count_result else 0
                    logger.info(f"  ✓ {table_name} ({count} 条记录)")
            
            return True
        except Exception as e:
            logger.error(f"检查数据库表失败: {e}", exc_info=True)
            return False
    
    async def migrate_users_table(self):
        """迁移users表 - 允许student_id为NULL"""
        logger.info("开始修复users表schema...")
        
        try:
            if not self.db_path.exists():
                logger.error(f"数据库文件不存在: {self.db_path}")
                return False
            
            # 使用sqlite3直接操作
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            if not cursor.fetchone():
                logger.info("users表不存在，将在下次init时创建")
                conn.close()
                return True
            
            logger.info("  [1/5] 创建临时表...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "users_new" (
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
                    "verification_code" VARCHAR(10),
                    "code_expires_at" TIMESTAMP,
                    "last_login" TIMESTAMP,
                    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "extra_info" JSON
                )
            """)
            
            logger.info("  [2/5] 检查现有数据...")
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.info(f"  [3/5] 复制 {count} 条现有数据...")
                # 先检查原表有哪些字段
                cursor.execute("PRAGMA table_info(users)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # 只复制存在的字段
                common_fields = [
                    'id', 'username', 'email', 'password', 'role', 
                    'student_id', 'real_name', 'class_id',
                    'is_active', 'is_email_verified', 'reset_token', 
                    'reset_token_expires', 'last_login', 
                    'created_at', 'updated_at', 'extra_info'
                ]
                # 添加新字段
                if 'verification_code' in columns:
                    pass
                else:
                    common_fields = [f for f in common_fields if f not in ['verification_code', 'code_expires_at']]
                
                existing_fields = [f for f in common_fields if f in columns]
                fields_str = ', '.join(existing_fields)
                
                cursor.execute(f"""
                    INSERT INTO users_new ({fields_str})
                    SELECT {fields_str} FROM users
                """)
            else:
                logger.info("  [3/5] 表中没有数据，跳过复制")
            
            logger.info("  [4/5] 删除旧表...")
            cursor.execute("DROP TABLE users")
            
            logger.info("  [5/5] 重命名新表...")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ users表修复成功！保留了 {count} 条用户记录")
            return True
            
        except Exception as e:
            logger.error(f"✗ 修复users表失败: {e}", exc_info=True)
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    async def migrate_academic_scores(self):
        """迁移创建academic_scores表"""
        logger.info("开始迁移academic_scores表...")
        
        try:
            conn = Tortoise.get_connection("default")
            
            # 检查并删除旧表
            logger.info("检查旧表...")
            
            old_tables = ['activities', 'score_records']
            for table_name in old_tables:
                table_exists = await conn.execute_query_dict(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                )
                
                if table_exists:
                    logger.info(f"  删除旧表 {table_name}...")
                    await conn.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                    logger.info(f"  ✓ {table_name}表已删除")
            
            # 检查academic_scores表
            logger.info("检查academic_scores表...")
            academic_scores_exists = await conn.execute_query_dict(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='academic_scores'"
            )
            
            if not academic_scores_exists:
                logger.info("  创建academic_scores表...")
                
                create_table_sql = """
                CREATE TABLE academic_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id VARCHAR(50) NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    college VARCHAR(100),
                    grade VARCHAR(20),
                    major VARCHAR(100),
                    class_name VARCHAR(50),
                    total_score REAL DEFAULT 0.0,
                    total_required_credits REAL DEFAULT 0.0,
                    course_count INTEGER DEFAULT 0,
                    total_credits REAL DEFAULT 0.0,
                    earned_credits REAL DEFAULT 0.0,
                    failed_credits REAL DEFAULT 0.0,
                    pass_rate REAL DEFAULT 0.0,
                    arithmetic_average REAL DEFAULT 0.0,
                    arithmetic_average_rank INTEGER,
                    weighted_average REAL DEFAULT 0.0,
                    weighted_average_rank INTEGER,
                    average_gpa REAL DEFAULT 0.0,
                    average_gpa_rank INTEGER,
                    average_credit_gpa REAL DEFAULT 0.0,
                    average_credit_gpa_rank INTEGER,
                    credit_gpa_sum REAL DEFAULT 0.0,
                    credit_gpa_sum_rank INTEGER,
                    failed_course_count INTEGER DEFAULT 0,
                    semester VARCHAR(20),
                    academic_year VARCHAR(20),
                    remarks TEXT,
                    details JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    UNIQUE (student_id, semester, academic_year)
                )
                """
                
                await conn.execute_query(create_table_sql)
                logger.info("  ✓ academic_scores表创建成功")
                
                # 创建索引
                logger.info("  创建索引...")
                await conn.execute_query(
                    "CREATE INDEX idx_academic_scores_student_id ON academic_scores(student_id)"
                )
                await conn.execute_query(
                    "CREATE INDEX idx_academic_scores_semester ON academic_scores(semester)"
                )
                await conn.execute_query(
                    "CREATE INDEX idx_academic_scores_class_name ON academic_scores(class_name)"
                )
                logger.info("  ✓ 索引创建成功")
            else:
                logger.info("  academic_scores表已存在，跳过创建")
            
            logger.info("✓ academic_scores表迁移完成")
            return True
            
        except Exception as e:
            logger.error(f"✗ 迁移academic_scores表失败: {e}", exc_info=True)
            return False
    
    async def migrate_comprehensive_config(self):
        """迁移创建综测配置表"""
        logger.info("开始迁移comprehensive_score_configs表...")
        
        try:
            conn = Tortoise.get_connection("default")
            
            # 检查表是否存在
            table_exists = await conn.execute_query_dict(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='comprehensive_score_configs'"
            )
            
            if not table_exists:
                logger.info("  创建comprehensive_score_configs表...")
                
                create_table_sql = """
                CREATE TABLE comprehensive_score_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    a_weight REAL DEFAULT 20.0,
                    b_weight REAL DEFAULT 70.0,
                    c_weight REAL DEFAULT 10.0,
                    academic_score_field VARCHAR(50) DEFAULT 'weighted_average',
                    academic_score_scale REAL DEFAULT 1.0,
                    is_active BOOLEAN DEFAULT 1,
                    is_default BOOLEAN DEFAULT 0,
                    applicable_grade VARCHAR(20),
                    applicable_semester VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                
                await conn.execute_query(create_table_sql)
                logger.info("  ✓ comprehensive_score_configs表创建成功")
                
                # 创建索引
                logger.info("  创建索引...")
                await conn.execute_query(
                    "CREATE INDEX idx_comp_score_configs_active ON comprehensive_score_configs(is_active)"
                )
                await conn.execute_query(
                    "CREATE INDEX idx_comp_score_configs_default ON comprehensive_score_configs(is_default)"
                )
                logger.info("  ✓ 索引创建成功")
                
                # 创建默认配置
                logger.info("  创建默认配置...")
                insert_default_sql = """
                INSERT INTO comprehensive_score_configs (
                    name, description, a_weight, b_weight, c_weight,
                    academic_score_field, academic_score_scale,
                    is_active, is_default
                ) VALUES (
                    '默认配置',
                    'A类20% + B类（学分加权平均分）70% + C类10%',
                    20.0, 70.0, 10.0,
                    'weighted_average', 1.0,
                    1, 1
                )
                """
                await conn.execute_query(insert_default_sql)
                logger.info("  ✓ 默认配置创建成功")
            else:
                logger.info("  comprehensive_score_configs表已存在，跳过创建")
            
            logger.info("✓ comprehensive_score_configs表迁移完成")
            return True
            
        except Exception as e:
            logger.error(f"✗ 迁移comprehensive_score_configs表失败: {e}", exc_info=True)
            return False
    
    async def migrate_all(self):
        """执行所有迁移"""
        logger.info("=" * 60)
        logger.info("开始执行所有数据库迁移...")
        logger.info("=" * 60)
        
        success = True
        
        # 1. 修复users表
        logger.info("\n[1/4] 修复users表schema...")
        if not await self.migrate_users_table():
            success = False
        
        # 2. 创建academic_scores表
        logger.info("\n[2/4] 创建academic_scores表...")
        if not await self.migrate_academic_scores():
            success = False
        
        # 3. 创建综测配置表
        logger.info("\n[3/4] 创建综测配置表...")
        if not await self.migrate_comprehensive_config():
            success = False
        
        # 4. 更新所有表结构
        logger.info("\n[4/4] 更新所有表结构...")
        if not await self.create_tables():
            success = False
        
        logger.info("\n" + "=" * 60)
        if success:
            logger.info("✓ 所有迁移执行完成！")
        else:
            logger.error("✗ 部分迁移执行失败，请检查日志")
        logger.info("=" * 60)
        
        return success
    
    async def backup_database(self):
        """备份数据库"""
        try:
            logger.info("开始备份数据库...")
            
            # 直接复制数据库文件
            backup_dir = self.db_path.parent
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"database_backup_{timestamp}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            logger.info(f"✓ 数据库备份完成: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"✗ 备份数据库失败: {e}", exc_info=True)
            return False
    
    async def reset_database(self):
        """重置数据库"""
        try:
            logger.info("开始重置数据库...")
            
            # 关闭现有连接
            await self.close_connection()
            
            # 删除数据库文件
            if self.db_path.exists():
                self.db_path.unlink()
                logger.info(f"  已删除数据库文件: {self.db_path}")
            
            # 重新初始化
            success = await self.init_connection()
            
            if success:
                logger.info("✓ 数据库重置完成")
                return True
            else:
                logger.error("✗ 数据库重置失败")
                return False
        except Exception as e:
            logger.error(f"✗ 重置数据库失败: {e}", exc_info=True)
            return False
    
    async def create_sample_data(self):
        """创建示例数据"""
        try:
            logger.info("开始创建示例数据...")
            
            # 创建示例学生
            from app.core.security import get_password_hash
            
            # 检查是否已有学生
            existing_students = await Student.all().count()
            if existing_students > 0:
                logger.info(f"  已存在 {existing_students} 个学生，跳过创建示例数据")
                return True
            
            logger.info("  创建示例学生...")
            student1 = await Student.create(
                id="20210001",
                name="张三",
                college="计算机学院",
                major="软件工程",
                class_name="软件2101",
                grade="2021"
            )
            
            student2 = await Student.create(
                id="20210002",
                name="李四",
                college="计算机学院",
                major="软件工程",
                class_name="软件2101",
                grade="2021"
            )
            
            logger.info("  创建示例用户...")
            await User.create(
                username="20210001",
                email="zhangsan@example.com",
                password=get_password_hash("password123"),
                role="student",
                student_id="20210001",
                real_name="张三",
                is_active=True
            )
            
            await User.create(
                username="20210002",
                email="lisi@example.com",
                password=get_password_hash("password123"),
                role="student",
                student_id="20210002",
                real_name="李四",
                is_active=True
            )
            
            # 创建管理员账户
            logger.info("  创建管理员账户...")
            await User.create(
                username="admin",
                email="admin@example.com",
                password=get_password_hash("admin123"),
                role="admin",
                real_name="管理员",
                is_active=True
            )
            
            logger.info("✓ 示例数据创建完成")
            logger.info("  学生账户: 20210001/password123, 20210002/password123")
            logger.info("  管理员账户: admin/admin123")
            return True
        except Exception as e:
            logger.error(f"✗ 创建示例数据失败: {e}", exc_info=True)
            return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="统一数据库管理和迁移脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python db_manager.py init              # 初始化数据库
  python db_manager.py check             # 检查数据库表
  python db_manager.py migrate           # 执行所有迁移
  python db_manager.py migrate-users     # 仅修复users表
  python db_manager.py migrate-academic  # 仅创建academic_scores表
  python db_manager.py migrate-config    # 仅创建综测配置表
  python db_manager.py backup            # 备份数据库
  python db_manager.py reset             # 重置数据库
  python db_manager.py sample            # 创建示例数据
        """
    )
    
    parser.add_argument(
        "command", 
        choices=[
            "init", "check", "migrate", 
            "migrate-users", "migrate-academic", "migrate-config",
            "backup", "reset", "sample"
        ],
        help="要执行的命令"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        import logging
        logger.setLevel(logging.DEBUG)
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    try:
        # 根据命令执行不同操作
        if args.command == "init":
            logger.info("=" * 60)
            logger.info("初始化数据库")
            logger.info("=" * 60)
            success = await db_manager.init_connection()
            if success:
                logger.info("\n✓ 数据库初始化成功")
                return 0
            else:
                logger.error("\n✗ 数据库初始化失败")
                return 1
        
        elif args.command == "check":
            logger.info("=" * 60)
            logger.info("检查数据库表")
            logger.info("=" * 60)
            await db_manager.init_connection()
            success = await db_manager.check_tables()
            return 0 if success else 1
        
        elif args.command == "migrate":
            if not args.yes:
                response = input("此操作将执行所有数据库迁移，是否继续？(yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    logger.info("操作已取消")
                    return 0
            
            await db_manager.init_connection()
            success = await db_manager.migrate_all()
            return 0 if success else 1
        
        elif args.command == "migrate-users":
            logger.info("=" * 60)
            logger.info("修复users表schema")
            logger.info("=" * 60)
            await db_manager.init_connection()
            success = await db_manager.migrate_users_table()
            return 0 if success else 1
        
        elif args.command == "migrate-academic":
            logger.info("=" * 60)
            logger.info("创建academic_scores表")
            logger.info("=" * 60)
            await db_manager.init_connection()
            success = await db_manager.migrate_academic_scores()
            return 0 if success else 1
        
        elif args.command == "migrate-config":
            logger.info("=" * 60)
            logger.info("创建综测配置表")
            logger.info("=" * 60)
            await db_manager.init_connection()
            success = await db_manager.migrate_comprehensive_config()
            return 0 if success else 1
        
        elif args.command == "backup":
            logger.info("=" * 60)
            logger.info("备份数据库")
            logger.info("=" * 60)
            await db_manager.init_connection()
            success = await db_manager.backup_database()
            return 0 if success else 1
        
        elif args.command == "reset":
            if not args.yes:
                response = input("⚠️  此操作将删除所有数据，是否继续？(yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    logger.info("操作已取消")
                    return 0
            
            logger.info("=" * 60)
            logger.info("重置数据库")
            logger.info("=" * 60)
            await db_manager.init_connection()
            success = await db_manager.reset_database()
            return 0 if success else 1
        
        elif args.command == "sample":
            logger.info("=" * 60)
            logger.info("创建示例数据")
            logger.info("=" * 60)
            await db_manager.init_connection()
            success = await db_manager.create_sample_data()
            return 0 if success else 1
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\n操作已取消")
        return 0
    except Exception as e:
        logger.error(f"\n执行失败: {e}", exc_info=True)
        return 1
    finally:
        # 关闭数据库连接
        try:
            await db_manager.close_connection()
        except:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

