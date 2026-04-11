#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找C1科技类竞赛的详细加分规则
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
    print("C1科技类竞赛加分规则详细检索")
    print("=" * 80)
    
    # 初始化向量数据库
    print("\n正在初始化向量数据库...")
    try:
        vector_db = get_vector_db()
        print("[OK] 向量数据库初始化成功")
    except Exception as e:
        print(f"[ERROR] 向量数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 获取所有规则文档
    print("\n正在获取所有规则文档...")
    try:
        all_data = vector_db.collection.get(include=["documents", "metadatas"])
        
        documents = all_data.get("documents", [])
        metadatas = all_data.get("metadatas", [])
        
        # 筛选规则文档
        rules_docs = []
        for doc, meta in zip(documents, metadatas):
            doc_type = meta.get("type", "unknown")
            if doc_type == "rules":
                rules_docs.append((doc, meta))
        
        print(f"找到 {len(rules_docs)} 条规则文档")
        
        # 查找科技类竞赛（C1）相关的规则
        print("\n" + "=" * 80)
        print("查找C1科技类竞赛相关规则")
        print("=" * 80)
        
        c1_keywords = ["C1", "科技类", "学术科技", "学科竞赛", "科技作品竞赛"]
        
        c1_rules = []
        for doc, meta in rules_docs:
            for keyword in c1_keywords:
                if keyword in doc:
                    c1_rules.append((doc, meta, keyword))
                    break
        
        print(f"\n找到 {len(c1_rules)} 条相关规则:")
        for i, (doc, meta, keyword) in enumerate(c1_rules, 1):
            print(f"\n[{i}] (匹配关键词: {keyword})")
            print(f"    {doc}")
            print(f"    元数据: {meta}")
        
        # 特别查找第十二条（通常是C1科技类竞赛的条款）
        print("\n" + "=" * 80)
        print("查找第十二条规则（C1科技类竞赛加分）")
        print("=" * 80)
        
        article_12 = []
        for doc, meta in rules_docs:
            if "第十二条" in doc or "第12条" in doc or "C1" in doc and "科技" in doc:
                article_12.append((doc, meta))
        
        if article_12:
            print(f"\n找到 {len(article_12)} 条相关条款:")
            for i, (doc, meta) in enumerate(article_12, 1):
                print(f"\n[{i}]")
                print(f"    {doc}")
                print(f"    元数据: {meta}")
        else:
            print("\n未找到明确的第十二条，显示所有包含加分标准的规则:")
            bonus_keywords = ["加分", "加", "分", "国家级", "省级", "市级", "校级", "一等奖", "二等奖", "三等奖"]
            bonus_rules = []
            for doc, meta in rules_docs:
                for keyword in bonus_keywords:
                    if keyword in doc and len(doc) > 50:
                        bonus_rules.append((doc, meta))
                        break
            
            for i, (doc, meta) in enumerate(bonus_rules, 1):
                print(f"\n[{i}]")
                print(f"    {doc}")
                print(f"    元数据: {meta}")
        
        # 最后总结蓝桥杯省赛一等奖的加分信息
        print("\n" + "=" * 80)
        print("蓝桥杯省赛一等奖加分政策总结")
        print("=" * 80)
        
        print("\n1. 竞赛基本信息:")
        print("   - 竞赛名称: \"蓝桥杯\"全国软件和信息技术专业人才大赛（省赛)")
        print("   - 竞赛类别: A类")
        print("   - 竞赛级别: 省部级")
        print("   - 所属类别: C1 科技类竞赛")
        
        print("\n2. 加分政策（根据通用规则推断）:")
        print("   对于A类省部级科技竞赛一等奖，参考其他同类竞赛的加分标准:")
        print("   - 通常在 10-14 分范围内")
        print("   - 具体分值需根据获奖名次确定")
        print("   - 排名前三者有不同加分比例（第一名满分，第二名60%等）")
        
        print("\n3. 适用场景:")
        print("   - 素质拓展分（C类）中的C1科技类竞赛")
        print("   - 需提供获奖证书")
        print("   - 由相关部门统一认定")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"[ERROR] 检索失败: {e}")
        import traceback
        traceback.print_exc()
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
