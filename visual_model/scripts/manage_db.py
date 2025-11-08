#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理脚本
用于初始化数据库、创建表、添加示例数据等
"""
import asyncio
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.logger import logger
from app.core.db_connection import get_db_connection_manager
from app.models.tortoise_models import (
    User, Student, Activity, ScoreRecord, 
    ComprehensiveScore, File
)
from app.services.database_tortoise import DatabaseService
from config import settings


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.db_manager = get_db_connection_manager()
        self.db_service = DatabaseService()
    
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
            logger.info("数据库表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}", exc_info=True)
            return False
    
    async def check_tables(self):
        """检查数据库表是否存在"""
        try:
            # 检查各个表是否存在
            tables_exist = True
            
            # 检查用户表
            try:
                await User.first()
                logger.info("用户表存在")
            except Exception:
                logger.warning("用户表不存在")
                tables_exist = False
            
            # 检查学生表
            try:
                await Student.first()
                logger.info("学生表存在")
            except Exception:
                logger.warning("学生表不存在")
                tables_exist = False
            
            # 检查活动表
            try:
                await Activity.first()
                logger.info("活动表存在")
            except Exception:
                logger.warning("活动表不存在")
                tables_exist = False
            
            # 检查分数记录表
            try:
                await ScoreRecord.first()
                logger.info("分数记录表存在")
            except Exception:
                logger.warning("分数记录表不存在")
                tables_exist = False
            
            # 检查综测成绩表
            try:
                await ComprehensiveScore.first()
                logger.info("综测成绩表存在")
            except Exception:
                logger.warning("综测成绩表不存在")
                tables_exist = False
            
            # 检查文件表
            try:
                await File.first()
                logger.info("文件表存在")
            except Exception:
                logger.warning("文件表不存在")
                tables_exist = False
            
            if tables_exist:
                logger.info("所有数据库表都存在")
            else:
                logger.warning("部分数据库表不存在")
            
            return tables_exist
        except Exception as e:
            logger.error(f"检查数据库表失败: {e}", exc_info=True)
            return False
    
    async def create_sample_data(self):
        """创建示例数据"""
        try:
            logger.info("开始创建示例数据")
            
            # 创建示例学生
            student1 = await self.db_service.create_student(
                id="20210001",
                name="张三",
                college="计算机学院",
                major="软件工程",
                class_name="软件2101",
                grade="2021"
            )
            
            student2 = await self.db_service.create_student(
                id="20210002",
                name="李四",
                college="计算机学院",
                major="软件工程",
                class_name="软件2101",
                grade="2021"
            )
            
            # 创建示例用户
            await self.db_service.create_user(
                student_id="20210001",
                password="password123",
                role="student"
            )
            
            await self.db_service.create_user(
                student_id="20210002",
                password="password123",
                role="student"
            )
            
            # 创建示例活动
            await self.db_service.create_activity(
                name="志愿服务",
                type="volunteer",
                details={"description": "校园志愿服务", "hours": 4},
                score=2.0,
                student_id="20210001",
                status="approved"
            )
            
            await self.db_service.create_activity(
                name="学科竞赛",
                type="competition",
                details={"description": "数学建模竞赛", "level": "省级", "award": "二等奖"},
                score=5.0,
                student_id="20210002",
                status="approved"
            )
            
            logger.info("示例数据创建完成")
            return True
        except Exception as e:
            logger.error(f"创建示例数据失败: {e}", exc_info=True)
            return False
    
    async def reset_database(self):
        """重置数据库"""
        try:
            logger.info("开始重置数据库")
            
            # 关闭现有连接
            await self.close_connection()
            
            # 删除数据库文件（SQLite）
            db_path = Path(settings.DATABASE_PATH)
            if db_path.exists():
                db_path.unlink()
                logger.info(f"已删除数据库文件: {db_path}")
            
            # 重新初始化并创建表（init_connection已包含create_tables）
            success = await self.init_connection()
            
            if success:
                logger.info("数据库重置完成")
                return True
            else:
                logger.error("数据库重置失败")
                return False
        except Exception as e:
            logger.error(f"重置数据库失败: {e}", exc_info=True)
            return False
    
    async def backup_database(self):
        """备份数据库"""
        try:
            logger.info("开始备份数据库")
            
            # 获取所有数据
            users = await User.all()
            students = await Student.all()
            activities = await Activity.all()
            score_records = await ScoreRecord.all()
            comprehensive_scores = await ComprehensiveScore.all()
            files = await File.all()
            
            # 创建备份数据
            from datetime import datetime
            import json
            
            backup_data = {
                "users": [user.__dict__ for user in users],
                "students": [student.__dict__ for student in students],
                "activities": [activity.__dict__ for activity in activities],
                "score_records": [record.__dict__ for record in score_records],
                "comprehensive_scores": [score.__dict__ for score in comprehensive_scores],
                "files": [file.__dict__ for file in files]
            }
            
            # 保存到文件
            backup_file = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"数据库备份完成，备份文件: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"备份数据库失败: {e}", exc_info=True)
            return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库管理脚本")
    parser.add_argument("command", choices=["init", "check", "sample", "reset", "backup", "migrate"], 
                       help="要执行的命令")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel("DEBUG")
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    try:
        # 根据命令执行不同操作
        if args.command == "init":
            # 初始化数据库（init_connection 已包含创建表的逻辑）
            logger.info("初始化数据库...")
            success = await db_manager.init_connection()
            if success:
                logger.info("数据库初始化成功")
            else:
                logger.error("数据库初始化失败")
                return 1
        
        elif args.command == "check":
            # 先连接数据库
            await db_manager.init_connection()
            # 检查数据库表
            logger.info("检查数据库表...")
            tables_exist = await db_manager.check_tables()
            if tables_exist:
                logger.info("所有数据库表都存在")
            else:
                logger.warning("部分数据库表不存在")
                return 1
        
        elif args.command == "sample":
            # 先连接数据库
            await db_manager.init_connection()
            # 创建示例数据
            logger.info("创建示例数据...")
            success = await db_manager.create_sample_data()
            if success:
                logger.info("示例数据创建成功")
            else:
                logger.error("示例数据创建失败")
                return 1
        
        elif args.command == "reset":
            # reset 会自己管理连接
            logger.info("重置数据库...")
            await db_manager.init_connection()
            success = await db_manager.reset_database()
            if success:
                logger.info("数据库重置成功")
            else:
                logger.error("数据库重置失败")
                return 1
        
        elif args.command == "backup":
            # 先连接数据库
            await db_manager.init_connection()
            # 备份数据库
            logger.info("备份数据库...")
            success = await db_manager.backup_database()
            if success:
                logger.info("数据库备份成功")
            else:
                logger.error("数据库备份失败")
                return 1
        
        elif args.command == "migrate":
            # 先连接数据库
            await db_manager.init_connection()
            # 数据库迁移
            logger.info("执行数据库迁移...")
            # 重新生成表结构
            await db_manager.create_tables()
            logger.info("数据库迁移完成")
        
        return 0
    
    finally:
        # 关闭数据库连接
        await db_manager.close_connection()


if __name__ == "__main__":
    # 运行主函数
    exit_code = asyncio.run(main())
    sys.exit(exit_code)