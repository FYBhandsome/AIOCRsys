#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 ChromaDB 向量数据库
解决 'dict' object has no attribute 'dimensionality' 错误
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

def backup_and_rebuild_vector_db():
    """备份并重建向量数据库"""
    
    db_path = Path(r'd:\AIOCR\PaddleOCRRAG\data\chroma_db')
    
    if not db_path.exists():
        print(f"数据库路径不存在: {db_path}")
        return False
    
    # 1. 备份现有数据库
    backup_dir = db_path.parent / f"chroma_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"正在备份数据库到: {backup_dir}")
    
    try:
        shutil.copytree(db_path, backup_dir)
        print("备份完成!")
    except Exception as e:
        print(f"备份失败: {e}")
        return False
    
    # 2. 删除损坏的数据库文件
    print("\n正在删除损坏的数据库文件...")
    try:
        shutil.rmtree(db_path)
        print("删除完成!")
    except Exception as e:
        print(f"删除失败: {e}")
        return False
    
    # 3. 重新创建数据库
    print("\n正在重新创建向量数据库...")
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 创建集合
        collection = client.get_or_create_collection(
            name="zongce_rules",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"数据库重建完成!")
        print(f"集合: {collection.name}")
        print(f"文档数: {collection.count()}")
        
        return True
        
    except Exception as e:
        print(f"重建失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ChromaDB 向量数据库修复工具")
    print("=" * 60)
    
    success = backup_and_rebuild_vector_db()
    
    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] 数据库修复成功!")
        print("请重新运行文档导入脚本以恢复数据")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[FAILED] 数据库修复失败!")
        print("=" * 60)
