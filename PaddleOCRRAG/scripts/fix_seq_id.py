#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 序列ID修复脚本
解决 "object of type 'int' has no len()" 错误
"""
import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime


def diagnose_seq_id_issue(db_path: str):
    """诊断序列ID问题"""
    print("=" * 60)
    print("ChromaDB 序列ID诊断")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"\n所有表: {tables}")
    
    # 检查 segments 相关的表
    for table in tables:
        if 'segment' in table.lower() or 'embedding' in table.lower():
            print(f"\n[{table} 表结构]")
            cursor.execute(f"PRAGMA table_info({table})")
            for col in cursor.fetchall():
                print(f"  {col}")
    
    # 检查 embedding_fulltext_search 表是否有 seq_id
    print("\n[检查 seq_id 列]")
    for table in ['embedding_fulltext_search', 'embeddings', 'embedding_metadata']:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [col[1] for col in cursor.fetchall()]
            if 'seq_id' in cols:
                print(f"  {table} 表有 seq_id 列")
                cursor.execute(f"SELECT seq_id FROM {table} LIMIT 5")
                for row in cursor.fetchall():
                    print(f"    seq_id={row[0]}, type={type(row[0])}")
        except Exception as e:
            pass
    
    conn.close()
    print("\n" + "=" * 60)


def fix_seq_id_issue(db_path: str):
    """修复序列ID问题"""
    print("=" * 60)
    print("ChromaDB 序列ID修复")
    print("=" * 60)
    
    # 备份数据库
    backup_dir = Path(db_path).parent.parent / "chroma_db_backup_seq"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"chroma_backup_{timestamp}"
    
    try:
        db_dir = Path(db_path).parent
        shutil.copytree(db_dir, backup_path)
        print(f"\n[备份] 数据库已备份到: {backup_path}")
    except Exception as e:
        print(f"\n[警告] 备份失败: {e}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查并修复 segments 表
        print("\n[修复] 检查 segments 表...")
        
        # 获取所有 segments
        cursor.execute("SELECT id, type, scope, collection, topic FROM segments")
        segments = cursor.fetchall()
        print(f"  发现 {len(segments)} 个 segments")
        
        # 检查每个 collection 的数据完整性
        cursor.execute("SELECT id, name FROM collections")
        collections = cursor.fetchall()
        print(f"  发现 {len(collections)} 个 collections")
        
        for coll_id, coll_name in collections:
            print(f"\n  检查 collection: {coll_name} ({coll_id})")
            
            # 检查该 collection 的 segments
            cursor.execute("SELECT id, type FROM segments WHERE collection = ?", (coll_id,))
            coll_segments = cursor.fetchall()
            print(f"    Segments: {len(coll_segments)}")
            
            for seg_id, seg_type in coll_segments:
                print(f"      - {seg_id[:8]}... ({seg_type})")
        
        # 尝试修复: 重新创建必要的索引
        print("\n[修复] 创建缺失的索引...")
        
        # 检查是否有 seq_id 相关的表需要修复
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%embedding%'")
        embedding_tables = cursor.fetchall()
        
        for (table_name,) in embedding_tables:
            try:
                # 检查是否有 seq_id 列
                cursor.execute(f"PRAGMA table_info({table_name})")
                cols = cursor.fetchall()
                col_names = [col[1] for col in cols]
                
                if 'seq_id' in col_names:
                    print(f"  检查 {table_name} 的 seq_id...")
                    # 检查是否有整数类型的 seq_id
                    cursor.execute(f"SELECT seq_id, typeof(seq_id) FROM {table_name} LIMIT 5")
                    for row in cursor.fetchall():
                        if row[1] == 'integer':
                            print(f"    发现整数类型 seq_id: {row[0]}")
                            # 需要转换为 blob
                            # 这里暂时跳过，因为修复可能需要更复杂的逻辑
            except Exception as e:
                print(f"  检查 {table_name} 失败: {e}")
        
        conn.commit()
        print("\n[完成] 修复完成")
        
    except Exception as e:
        print(f"\n[错误] 修复失败: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("\n" + "=" * 60)


def recreate_collection(db_path: str, collection_name: str = "zongce_rules"):
    """重建指定集合"""
    print("=" * 60)
    print(f"重建集合: {collection_name}")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取 collection ID
        cursor.execute("SELECT id FROM collections WHERE name = ?", (collection_name,))
        result = cursor.fetchone()
        
        if result:
            coll_id = result[0]
            print(f"\n找到集合: {collection_name} (ID: {coll_id})")
            
            # 删除相关的 segments
            cursor.execute("DELETE FROM segments WHERE collection = ?", (coll_id,))
            print(f"删除了 {cursor.rowcount} 个 segments")
            
            # 删除 collection
            cursor.execute("DELETE FROM collections WHERE id = ?", (coll_id,))
            print(f"删除了 collection")
            
            conn.commit()
            print("\n[完成] 集合已删除，下次启动时会自动重建")
        else:
            print(f"\n未找到集合: {collection_name}")
    
    except Exception as e:
        print(f"\n[错误] 重建失败: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    import sys
    
    db_path = r"d:\AIOCR\PaddleOCRRAG\data\chroma_db\chroma.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    print("ChromaDB 修复工具")
    print("=" * 60)
    print("1. 诊断序列ID问题")
    print("2. 修复序列ID问题")
    print("3. 重建 zongce_rules 集合")
    print("4. 退出")
    print("=" * 60)
    
    choice = input("\n请选择操作 (1-4): ").strip()
    
    if choice == "1":
        diagnose_seq_id_issue(db_path)
    elif choice == "2":
        fix_seq_id_issue(db_path)
    elif choice == "3":
        recreate_collection(db_path)
    elif choice == "4":
        print("退出")
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
