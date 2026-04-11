#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 数据库修复脚本
========================
解决 "no such column: collections.topic" 错误

问题原因：
    ChromaDB 0.4.24 版本需要 collections 表包含 topic 字段，
    但旧版本数据库缺少该字段。

解决方案：
    1. 备份现有数据
    2. 添加缺失的 topic 字段
    3. 创建缺失的 tenants 和 databases 表（如果需要）
    4. 验证修复结果

使用方法：
    python scripts/fix_chroma_db.py
"""

import sqlite3
import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional


class ChromaDBFixer:
    """ChromaDB 数据库修复工具"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.chroma_sqlite = self.db_path / "chroma.sqlite3"
        self.backup_dir = self.db_path.parent / "chroma_db_backup"
        
    def check_database_exists(self) -> bool:
        """检查数据库文件是否存在"""
        return self.chroma_sqlite.exists()
    
    def get_table_structure(self, table_name: str) -> List[Tuple]:
        """获取表结构"""
        if not self.check_database_exists():
            return []
        
        conn = sqlite3.connect(str(self.chroma_sqlite))
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        return columns
    
    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        if not self.check_database_exists():
            return []
        
        conn = sqlite3.connect(str(self.chroma_sqlite))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    
    def has_topic_column(self, table_name: str = "collections") -> bool:
        """检查指定表是否有 topic 字段"""
        columns = self.get_table_structure(table_name)
        for col in columns:
            if col[1] == "topic":
                return True
        return False
    
    def check_segments_topic(self) -> bool:
        """检查 segments 表是否有 topic 字段"""
        return self.has_topic_column("segments")
    
    def has_required_tables(self) -> Tuple[bool, bool]:
        """检查是否有必需的表"""
        tables = self.get_all_tables()
        has_tenants = "tenants" in tables
        has_databases = "databases" in tables
        return has_tenants, has_databases
    
    def backup_database(self) -> Optional[str]:
        """备份数据库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"chroma_backup_{timestamp}"
        
        try:
            shutil.copytree(self.db_path, backup_path)
            print(f"[OK] 数据库已备份到: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"[ERROR] 备份失败: {e}")
            return None
    
    def fix_database(self) -> bool:
        """修复数据库"""
        if not self.check_database_exists():
            print("[ERROR] 数据库文件不存在")
            return False
        
        conn = sqlite3.connect(str(self.chroma_sqlite))
        cursor = conn.cursor()
        
        try:
            has_tenants, has_databases = self.has_required_tables()
            has_collections_topic = self.has_topic_column("collections")
            has_segments_topic = self.has_topic_column("segments")
            
            if has_collections_topic and has_segments_topic and has_tenants and has_databases:
                print("[INFO] 数据库结构已正确，无需修复")
                return True
            
            print("[INFO] 开始修复数据库结构...")
            
            if not has_tenants:
                print("[INFO] 创建 tenants 表...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tenants (
                        id TEXT PRIMARY KEY,
                        UNIQUE (id)
                    )
                """)
                cursor.execute("""
                    INSERT OR REPLACE INTO tenants (id) VALUES ('default_tenant')
                """)
            
            if not has_databases:
                print("[INFO] 创建 databases 表...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS databases (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                        UNIQUE (tenant_id, name)
                    )
                """)
                cursor.execute("""
                    INSERT OR REPLACE INTO databases (id, name, tenant_id) 
                    VALUES ('00000000-0000-0000-0000-000000000000', 'default_database', 'default_tenant')
                """)
            
            if not has_collections_topic:
                print("[INFO] 添加 topic 字段到 collections 表...")
                cursor.execute("""
                    ALTER TABLE collections ADD COLUMN topic TEXT DEFAULT ''
                """)
                
                print("[INFO] 更新 collections 表现有记录的 topic 字段...")
                cursor.execute("""
                    UPDATE collections SET topic = 'topic_' || id WHERE topic = '' OR topic IS NULL
                """)
            
            if not has_segments_topic:
                print("[INFO] 添加 topic 字段到 segments 表...")
                try:
                    cursor.execute("""
                        ALTER TABLE segments ADD COLUMN topic TEXT DEFAULT ''
                    """)
                    
                    print("[INFO] 更新 segments 表现有记录的 topic 字段...")
                    cursor.execute("""
                        UPDATE segments SET topic = 'topic_' || collection WHERE topic = '' OR topic IS NULL
                    """)
                except sqlite3.OperationalError as e:
                    print(f"[WARN] segments 表可能不存在或已修复: {e}")
            
            if not has_databases:
                print("[INFO] 添加 database_id 字段到 collections 表（如果不存在）...")
                try:
                    cursor.execute("""
                        ALTER TABLE collections ADD COLUMN database_id TEXT DEFAULT '00000000-0000-0000-0000-000000000000'
                    """)
                except sqlite3.OperationalError:
                    pass
            
            conn.commit()
            print("[OK] 数据库修复完成!")
            return True
            
        except Exception as e:
            print(f"[ERROR] 修复失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def verify_fix(self) -> bool:
        """验证修复结果"""
        if not self.check_database_exists():
            return False
        
        conn = sqlite3.connect(str(self.chroma_sqlite))
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(collections)")
            collections_columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = ['id', 'name', 'topic']
            missing = [col for col in required_columns if col not in collections_columns]
            
            if missing:
                print(f"[ERROR] collections 表仍然缺少字段: {missing}")
                return False
            
            cursor.execute("PRAGMA table_info(segments)")
            segments_columns = [col[1] for col in cursor.fetchall()]
            
            if 'topic' not in segments_columns:
                print("[ERROR] segments 表缺少 topic 字段")
                return False
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'tenants' not in tables or 'databases' not in tables:
                print("[ERROR] 缺少必需的表")
                return False
            
            print("[OK] 数据库结构验证通过!")
            print(f"  - collections 表字段: {collections_columns}")
            print(f"  - segments 表字段: {segments_columns}")
            print(f"  - 已有表: {tables}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 验证失败: {e}")
            return False
        finally:
            conn.close()
    
    def run(self) -> bool:
        """执行完整修复流程"""
        print("=" * 60)
        print("ChromaDB 数据库修复工具")
        print("=" * 60)
        
        print(f"\n[INFO] 数据库路径: {self.chroma_sqlite}")
        
        if not self.check_database_exists():
            print("[ERROR] 数据库文件不存在，请先启动服务创建数据库")
            return False
        
        print("\n[步骤 1] 检查当前数据库状态...")
        has_tenants, has_databases = self.has_required_tables()
        has_collections_topic = self.has_topic_column("collections")
        has_segments_topic = self.has_topic_column("segments")
        
        print(f"  - tenants 表: {'存在' if has_tenants else '缺失'}")
        print(f"  - databases 表: {'存在' if has_databases else '缺失'}")
        print(f"  - collections.topic 字段: {'存在' if has_collections_topic else '缺失'}")
        print(f"  - segments.topic 字段: {'存在' if has_segments_topic else '缺失'}")
        
        if has_collections_topic and has_segments_topic and has_tenants and has_databases:
            print("\n[INFO] 数据库结构正确，无需修复")
            return True
        
        print("\n[步骤 2] 备份数据库...")
        backup_path = self.backup_database()
        if backup_path is None:
            print("[WARN] 备份失败，是否继续? (y/n): ", end="")
            choice = input().strip().lower()
            if choice != 'y':
                return False
        
        print("\n[步骤 3] 执行修复...")
        if not self.fix_database():
            return False
        
        print("\n[步骤 4] 验证修复结果...")
        if not self.verify_fix():
            return False
        
        print("\n" + "=" * 60)
        print("[SUCCESS] 数据库修复成功!")
        print("=" * 60)
        return True


def main():
    """主函数"""
    import sys
    
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "chroma_db"
    
    fixer = ChromaDBFixer(str(db_path))
    success = fixer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
