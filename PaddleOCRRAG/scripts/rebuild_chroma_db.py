#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全重建 ChromaDB 向量数据库
解决 'dict' object has no attribute 'dimensionality' 错误
"""
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

def rebuild_chroma_db():
    """完全重建 ChromaDB"""
    
    db_path = Path(r'd:\AIOCR\PaddleOCRRAG\data\chroma_db')
    
    print("=" * 60)
    print("ChromaDB 完全重建工具")
    print("=" * 60)
    
    # 1. 备份现有数据库
    if db_path.exists():
        backup_dir = db_path.parent / f"chroma_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n[1/4] 正在备份数据库到: {backup_dir}")
        
        try:
            shutil.copytree(db_path, backup_dir)
            print("      备份完成!")
        except Exception as e:
            print(f"      备份失败: {e}")
            return False
        
        # 2. 删除所有文件
        print("\n[2/4] 正在删除旧数据库文件...")
        try:
            # 先关闭所有连接
            for file in db_path.glob("*.sqlite3"):
                try:
                    conn = sqlite3.connect(str(file))
                    conn.close()
                except:
                    pass
            
            shutil.rmtree(db_path)
            print("      删除完成!")
        except Exception as e:
            print(f"      删除失败: {e}")
            # 尝试强制删除
            try:
                os.system(f'rmdir /s /q "{db_path}"')
                print("      强制删除完成!")
            except Exception as e2:
                print(f"      强制删除也失败: {e2}")
                return False
    
    # 3. 创建新数据库
    print("\n[3/4] 正在创建新数据库...")
    try:
        import chromadb
        from chromadb.config import Settings
        
        db_path.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 创建集合
        collection = client.get_or_create_collection(
            name="zongce_rules",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"      数据库创建成功!")
        print(f"      集合: {collection.name}")
        print(f"      文档数: {collection.count()}")
        
    except Exception as e:
        print(f"      创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 验证数据库
    print("\n[4/4] 正在验证数据库...")
    try:
        # 测试查询
        results = collection.query(
            query_texts=["测试查询"],
            n_results=1
        )
        print("      数据库验证成功!")
        print("      查询功能正常!")
        
    except Exception as e:
        print(f"      验证失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 数据库重建完成!")
    print("请运行以下命令导入规则文档:")
    print("  python scripts/vectorize_documents.py --directory data/rules")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    rebuild_chroma_db()
