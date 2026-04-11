#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出数据库中所有竞赛信息
"""

import sys
import os
from pathlib import Path

# 添加PaddleOCRRAG目录到路径
RAG_DIR = Path(__file__).parent / "PaddleOCRRAG"
sys.path.insert(0, str(RAG_DIR))

try:
    from app.rag.vector_db.vector_db import get_vector_db
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)


def main():
    print("=" * 80)
    print("数据库中所有竞赛信息")
    print("=" * 80)
    
    # 初始化向量数据库
    print("\n正在初始化向量数据库...")
    try:
        vector_db = get_vector_db()
        print("[OK] 向量数据库初始化成功")
    except Exception as e:
        print(f"[ERROR] 向量数据库初始化失败: {e}")
        return 1
    
    # 获取所有文档
    print("\n正在获取所有文档...")
    try:
        all_data = vector_db.collection.get(include=["documents", "metadatas"])
        
        documents = all_data.get("documents", [])
        metadatas = all_data.get("metadatas", [])
        ids = all_data.get("ids", [])
        
        print(f"[OK] 总共找到 {len(documents)} 条文档")
        
        # 分类显示
        competition_list = []
        rules_list = []
        
        for doc, meta, doc_id in zip(documents, metadatas, ids):
            doc_type = meta.get("type", "unknown")
            if doc_type == "competition_list":
                competition_list.append((doc, meta, doc_id))
            elif doc_type == "rules":
                rules_list.append((doc, meta, doc_id))
        
        print(f"\n--- 竞赛列表 ({len(competition_list)} 条) ---")
        for i, (doc, meta, doc_id) in enumerate(competition_list, 1):
            print(f"\n{i}. {doc}")
            print(f"   元数据: {meta}")
        
        print(f"\n--- 规则文档 ({len(rules_list)} 条) ---")
        for i, (doc, meta, doc_id) in enumerate(rules_list[:20], 1):  # 只显示前20条
            print(f"\n{i}. {doc[:100]}..." if len(doc) > 100 else f"\n{i}. {doc}")
            print(f"   元数据: {meta}")
        
        if len(rules_list) > 20:
            print(f"\n... 还有 {len(rules_list) - 20} 条规则文档")
        
    except Exception as e:
        print(f"[ERROR] 获取文档失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
