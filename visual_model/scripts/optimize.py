#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目优化脚本

用于定期清理和优化项目代码。
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Set

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logger import logger


class ProjectOptimizer:
    """项目优化器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.temp_dirs = {
            "temp", "tmp", "__pycache__", ".pytest_cache", 
            "node_modules", ".git", ".vscode", ".idea"
        }
        self.temp_files = {
            ".pyc", ".pyo", ".pyd", ".log", ".tmp", 
            ".DS_Store", "Thumbs.db", ".env.local"
        }
    
    def clean_temp_files(self) -> int:
        """清理临时文件"""
        cleaned_count = 0
        
        for root, dirs, files in os.walk(self.project_root):
            # 跳过特定目录
            dirs[:] = [d for d in dirs if d not in self.temp_dirs]
            
            # 清理临时文件
            for file in files:
                file_path = Path(root) / file
                if any(file.endswith(ext) for ext in self.temp_files):
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"删除临时文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除文件失败: {file_path}, 错误: {e}")
        
        return cleaned_count
    
    def clean_empty_dirs(self) -> int:
        """清理空目录"""
        cleaned_count = 0
        
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        cleaned_count += 1
                        logger.info(f"删除空目录: {dir_path}")
                except Exception as e:
                    logger.warning(f"删除目录失败: {dir_path}, 错误: {e}")
        
        return cleaned_count
    
    def check_unused_imports(self) -> List[str]:
        """检查未使用的导入（简单检查）"""
        unused_imports = []
        
        for py_file in self.project_root.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单的未使用导入检查
                lines = content.split('\n')
                imports = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line)
                
                # 这里可以添加更复杂的检查逻辑
                # 目前只是收集导入语句
                
            except Exception as e:
                logger.warning(f"检查文件失败: {py_file}, 错误: {e}")
        
        return unused_imports
    
    def optimize_database(self) -> bool:
        """优化数据库（如果是SQLite）"""
        try:
            from config import settings
            
            if "sqlite" in settings.DATABASE_URL.lower():
                import sqlite3
                
                # 提取数据库文件路径
                db_path = settings.DATABASE_URL.replace("sqlite:///", "")
                if Path(db_path).exists():
                    conn = sqlite3.connect(db_path)
                    conn.execute("VACUUM")
                    conn.close()
                    logger.info("SQLite数据库已优化")
                    return True
            
        except Exception as e:
            logger.warning(f"数据库优化失败: {e}")
        
        return False
    
    def generate_report(self) -> dict:
        """生成优化报告"""
        report = {
            "temp_files_cleaned": 0,
            "empty_dirs_cleaned": 0,
            "database_optimized": False,
            "project_size": 0,
            "recommendations": []
        }
        
        # 清理临时文件
        report["temp_files_cleaned"] = self.clean_temp_files()
        
        # 清理空目录
        report["empty_dirs_cleaned"] = self.clean_empty_dirs()
        
        # 优化数据库
        report["database_optimized"] = self.optimize_database()
        
        # 计算项目大小
        total_size = 0
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        report["project_size"] = total_size
        
        # 生成建议
        if report["temp_files_cleaned"] > 0:
            report["recommendations"].append("定期清理临时文件以节省空间")
        
        if total_size > 1024 * 1024 * 100:  # 100MB
            report["recommendations"].append("项目较大，考虑清理不必要的文件")
        
        return report


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    optimizer = ProjectOptimizer(project_root)
    
    logger.info("开始项目优化...")
    
    # 生成优化报告
    report = optimizer.generate_report()
    
    # 输出报告
    logger.info("=== 项目优化报告 ===")
    logger.info(f"清理临时文件: {report['temp_files_cleaned']} 个")
    logger.info(f"清理空目录: {report['empty_dirs_cleaned']} 个")
    logger.info(f"数据库优化: {'成功' if report['database_optimized'] else '跳过'}")
    logger.info(f"项目大小: {report['project_size'] / 1024 / 1024:.2f} MB")
    
    if report["recommendations"]:
        logger.info("优化建议:")
        for rec in report["recommendations"]:
            logger.info(f"  - {rec}")
    
    logger.info("项目优化完成!")


if __name__ == "__main__":
    main()
