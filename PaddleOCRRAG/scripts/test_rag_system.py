#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统测试脚本 - 使用.conda环境运行
测试RAG向量数据库功能和检索功能
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent / "PaddleOCRRAG"
sys.path.insert(0, str(PROJECT_ROOT))


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def print_sub_separator(title: str = ""):
    """打印子分隔线"""
    print("\n" + "-" * 60)
    if title:
        print(f"  {title}")
        print("-" * 60)


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def test_rag_vector_db():
    """测试RAG向量数据库"""
    print_separator("RAG 向量数据库详细测试")
    
    try:
        from app.rag.vector_db.vector_db import get_vector_db
        from app.core.config_manager import settings
        
        print("\n【RAG 配置信息】")
        print(f"  ├─ 向量数据库路径: {settings.CHROMA_DB_PATH}")
        print(f"  ├─ 规则文档路径: {settings.RULES_DOCS_PATH}")
        print(f"  ├─ 嵌入模型: {settings.EMBEDDING_MODEL}")
        print(f"  ├─ 嵌入设备: {settings.EMBEDDING_DEVICE}")
        print(f"  ├─ HuggingFace镜像: {settings.HF_ENDPOINT}")
        print(f"  └─ Top-K检索数: {settings.TOP_K}")
        
        print_sub_separator("初始化向量数据库")
        print("\n正在初始化向量数据库...")
        start_time = time.time()
        
        vector_db = get_vector_db()
        
        init_duration = time.time() - start_time
        print(f"向量数据库初始化完成 (耗时: {init_duration:.2f}秒)")
        
        print_sub_separator("获取向量数据库统计信息")
        
        stats = vector_db.get_category_stats()
        
        print("\n【向量数据库统计】")
        print(f"  ├─ 总文档数: {stats.get('total', 0)}")
        
        if 'by_type' in stats:
            print(f"\n  按类型分布:")
            for doc_type, count in stats['by_type'].items():
                print(f"    ├─ {doc_type}: {count}")
        
        if 'by_main_category' in stats:
            print(f"\n  按主类别分布:")
            for cat, count in stats['by_main_category'].items():
                print(f"    ├─ {cat}: {count}")
        
        if 'by_sub_category' in stats:
            print(f"\n  按子类别分布:")
            for cat, count in stats['by_sub_category'].items():
                print(f"    ├─ {cat}: {count}")
        
        if 'by_competition_type' in stats:
            print(f"\n  按竞赛类型分布:")
            for comp_type, count in stats['by_competition_type'].items():
                print(f"    ├─ {comp_type}: {count}")
        
        if 'by_level' in stats:
            print(f"\n  按级别分布:")
            for level, count in stats['by_level'].items():
                print(f"    ├─ {level}: {count}")
        
        print(f"\n  需人工审核数: {stats.get('manual_review_count', 0)}")
        
        print_sub_separator("向量索引信息")
        print(f"\n  ├─ 集合名称: {vector_db.collection_name}")
        print(f"  ├─ 索引类型: HNSW (Hierarchical Navigable Small World)")
        print(f"  ├─ 相似度度量: Cosine (余弦相似度)")
        print(f"  └─ 嵌入维度: 384 (all-MiniLM-L6-v2) 或 768 (bge-small-zh)")
        
        return {
            "success": True,
            "stats": stats,
            "init_duration_seconds": round(init_duration, 2)
        }
        
    except Exception as e:
        print(f"\n✗ RAG向量数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_rag_retrieval():
    """测试RAG检索功能"""
    print_separator("RAG 检索功能测试")
    
    try:
        from app.rag.vector_db.vector_db import get_vector_db
        
        vector_db = get_vector_db()
        
        test_queries = [
            "综测计算细则",
            "省级竞赛一等奖加多少分",
            "英语四级可以加多少分",
            "社会实践要求多少学时",
            "创新创业加分规则",
            "蓝桥杯竞赛加分",
            "计算机二级证书加分"
        ]
        
        print("\n【检索测试】")
        
        results = []
        for query in test_queries:
            print_sub_separator(f"查询: {query}")
            
            start_time = time.time()
            search_result = vector_db.search_relevant(query, top_k=3)
            duration = time.time() - start_time
            
            documents = search_result.get("documents", [])
            metadatas = search_result.get("metadatas", [])
            distances = search_result.get("distances", [])
            
            if documents and len(documents) > 0:
                print(f"\n  找到 {len(documents)} 条相关结果 (耗时: {duration*1000:.2f}ms)")
                
                for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
                    print(f"\n  结果 #{i+1}:")
                    print(f"    ├─ 相似度距离: {dist:.4f}")
                    print(f"    ├─ 类型: {meta.get('type', 'N/A')}")
                    print(f"    ├─ 主类别: {meta.get('main_category', 'N/A')}")
                    print(f"    ├─ 子类别: {meta.get('sub_category', 'N/A')}")
                    if meta.get('competition_type'):
                        print(f"    ├─ 竞赛类型: {meta.get('competition_type')}")
                    if meta.get('level'):
                        print(f"    ├─ 级别: {meta.get('level')}")
                    if meta.get('score'):
                        print(f"    ├─ 分数: {meta.get('score')}")
                    print(f"    └─ 内容摘要: {doc[:150]}...")
            else:
                print(f"\n  未找到相关结果")
            
            results.append({
                "query": query,
                "result_count": len(documents) if documents else 0,
                "duration_ms": round(duration * 1000, 2)
            })
        
        return {
            "success": True,
            "test_queries": results
        }
        
    except Exception as e:
        print(f"\n✗ RAG检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_category_aware_search():
    """测试类别感知检索"""
    print_separator("RAG 类别感知检索测试")
    
    try:
        from app.rag.vector_db.vector_db import get_vector_db
        
        vector_db = get_vector_db()
        
        test_cases = [
            ("蓝桥杯省赛一等奖能加多少分", "竞赛加分查询"),
            ("英语六级证书加分标准", "证书加分查询"),
            ("C1类科技竞赛有哪些", "类别规则查询"),
        ]
        
        print("\n【类别感知检索测试】")
        
        for query, description in test_cases:
            print_sub_separator(f"{description}: {query}")
            
            start_time = time.time()
            results, intent = vector_db.search_with_category_awareness(query, top_k=3)
            duration = time.time() - start_time
            
            print(f"\n  意图识别结果:")
            print(f"    ├─ 主类别: {intent.main_category}")
            print(f"    ├─ 子类别: {intent.sub_category}")
            print(f"    ├─ 竞赛类型: {intent.competition_type or 'N/A'}")
            print(f"    ├─ 置信度: {intent.confidence:.2f}")
            print(f"    └─ 需人工审核: {intent.requires_manual_review}")
            
            print(f"\n  检索结果 ({len(results)}条, 耗时: {duration*1000:.2f}ms):")
            
            for i, result in enumerate(results[:3]):
                print(f"\n  结果 #{i+1}:")
                print(f"    ├─ 重排得分: {result.reranked_score:.4f}")
                print(f"    ├─ 原始距离: {result.original_distance:.4f}")
                print(f"    └─ 内容摘要: {result.document[:100]}...")
        
        return {"success": True}
        
    except Exception as e:
        print(f"\n✗ 类别感知检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_documents_info():
    """测试文档信息"""
    print_separator("RAG 文档信息测试")
    
    rules_dir = PROJECT_ROOT / "data" / "rules"
    
    print(f"\n【规则文档目录】")
    print(f"  路径: {rules_dir}")
    
    if rules_dir.exists():
        print(f"\n【目录状态】: 存在 ✓")
        
        print_sub_separator("规则文档详情")
        
        total_size = 0
        doc_count = 0
        
        for doc in sorted(rules_dir.iterdir()):
            if doc.is_file() and not doc.name.startswith('.'):
                doc_count += 1
                size = doc.stat().st_size
                total_size += size
                mod_time = datetime.fromtimestamp(doc.stat().st_mtime)
                
                print(f"\n  文档 #{doc_count}: {doc.name}")
                print(f"    ├─ 类型: {doc.suffix.upper()}")
                print(f"    ├─ 大小: {format_size(size)}")
                print(f"    └─ 修改时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print_sub_separator("文档统计汇总")
        print(f"\n  ├─ 文档总数: {doc_count}")
        print(f"  └─ 总大小: {format_size(total_size)}")
        
        return {"success": True, "doc_count": doc_count, "total_size": total_size}
    else:
        print(f"\n【目录状态】: 不存在")
        return {"success": True, "doc_count": 0}


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("  RAG系统 - 全面功能测试")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = {}
    
    results["documents_info"] = test_documents_info()
    results["vector_db"] = test_rag_vector_db()
    results["retrieval"] = test_rag_retrieval()
    results["category_aware"] = test_category_aware_search()
    
    print_separator("测试结果汇总")
    
    test_names = {
        "documents_info": "文档信息",
        "vector_db": "向量数据库",
        "retrieval": "检索功能",
        "category_aware": "类别感知检索"
    }
    
    passed = 0
    total = len(results)
    
    for key, result in results.items():
        success = result.get("success", False) if isinstance(result, dict) else result
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status}: {test_names.get(key, key)}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"通过率: {passed/total*100:.1f}%")
    
    return results


if __name__ == "__main__":
    run_all_tests()
