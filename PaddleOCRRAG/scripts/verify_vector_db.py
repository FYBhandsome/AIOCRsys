#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库验证脚本
检查向量库是否正确存储了rules目录下的信息
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from chromadb.config import Settings

def check_vector_db():
    """检查向量数据库"""
    print("=" * 60)
    print("向量数据库验证")
    print("=" * 60)
    
    db_path = project_root / "data" / "chroma_db"
    print(f"\n向量数据库路径: {db_path}")
    
    if not db_path.exists():
        print("❌ 向量数据库目录不存在!")
        return False
    
    try:
        client = chromadb.PersistentClient(path=str(db_path))
        
        collections = client.list_collections()
        print(f"\n集合数量: {len(collections)}")
        
        for coll in collections:
            print(f"\n--- 集合: {coll.name} ---")
            count = coll.count()
            print(f"文档数量: {count}")
            
            if count > 0:
                results = coll.get(limit=5, include=["documents", "metadatas"])
                print(f"示例文档 (前5个):")
                for i, doc in enumerate(results["documents"][:5]):
                    print(f"  [{i+1}] {doc[:100]}..." if len(doc) > 100 else f"  [{i+1}] {doc}")
                    if results["metadatas"] and i < len(results["metadatas"]):
                        print(f"      元数据: {results['metadatas'][i]}")
        
        print("\n" + "=" * 60)
        print("✓ 向量数据库验证完成")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def check_rules_docs():
    """检查rules目录文档"""
    print("\n" + "=" * 60)
    print("Rules目录文档检查")
    print("=" * 60)
    
    rules_path = project_root / "data" / "rules"
    print(f"\nRules路径: {rules_path}")
    
    if not rules_path.exists():
        print("❌ Rules目录不存在!")
        return False
    
    files = list(rules_path.glob("*"))
    print(f"\n文件数量: {len(files)}")
    
    for f in files:
        if f.is_file():
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
    
    return True


def check_document_meta():
    """检查文档元数据"""
    print("\n" + "=" * 60)
    print("文档元数据检查")
    print("=" * 60)
    
    import json
    meta_path = project_root / "data" / "document_meta.json"
    
    if not meta_path.exists():
        print("❌ 文档元数据文件不存在!")
        return False
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    print(f"\n已注册文档数量: {len(meta)}")
    
    for doc_id, doc_info in meta.items():
        print(f"\n  文档ID: {doc_id}")
        print(f"    原始名称: {doc_info.get('original_name')}")
        print(f"    文件路径: {doc_info.get('file_path')}")
        print(f"    状态: {'启用' if doc_info.get('enabled') else '禁用'}")
        print(f"    切片数量: {doc_info.get('chunk_count', 0)}")
    
    return True


if __name__ == "__main__":
    check_rules_docs()
    check_document_meta()
    check_vector_db()
