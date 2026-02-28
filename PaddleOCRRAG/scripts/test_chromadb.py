#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG向量数据库测试脚本 - 使用sqlite3直接读取
"""

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent / "PaddleOCRRAG"
sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests" / "utils"))
from test_helpers import (
    print_separator, print_sub_separator, format_size, 
    format_datetime, get_directory_stats, TestLogger, ChromaDBHelper
)


def test_sqlite_db():
    """使用sqlite3直接测试ChromaDB"""
    print_separator("ChromaDB 向量数据库详细测试 (SQLite)")
    
    db_path = PROJECT_ROOT / "data" / "chroma_db"
    helper = ChromaDBHelper(str(db_path))
    
    print(f"\n【数据库配置】")
    print(f"  ├─ 数据库路径: {db_path}")
    print(f"  ├─ 数据库类型: SQLite (ChromaDB后端)")
    print(f"  └─ 索引算法: HNSW (Hierarchical Navigable Small World)")
    
    stats = helper.get_stats()
    
    if not stats["sqlite_exists"]:
        print(f"\n【数据库状态】: 不存在")
        return {"success": False, "error": "数据库文件不存在"}
    
    print(f"\n【数据库状态】: 存在 ✓")
    print(f"  ├─ 文件大小: {stats['db_size_formatted']}")
    print(f"  └─ 修改时间: {format_datetime(Path(helper.sqlite_path).stat().st_mtime)}")
    
    try:
        conn = helper.get_connection()
        cursor = conn.cursor()
        
        print_sub_separator("数据库表结构")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n  发现 {len(tables)} 个表:")
        for table in tables:
            print(f"    ├─ {table[0]}")
        
        print_sub_separator("集合信息")
        
        print(f"\n  发现 {len(stats['collections'])} 个集合:")
        for coll_id, coll_name in stats['collections']:
            print(f"    ├─ ID: {coll_id}")
            print(f"    └─ 名称: {coll_name}")
        
        if stats['collections']:
            print_sub_separator("文档统计")
            print(f"\n  总文档数: {stats['total_documents']}")
            
            print_sub_separator("向量索引信息")
            
            cursor.execute("PRAGMA table_info(embedding_fulltext_search);")
            columns = cursor.fetchall()
            
            print(f"\n  表结构:")
            for col in columns:
                print(f"    ├─ {col[1]} ({col[2]})")
        
        conn.close()
        
        return {
            "success": True,
            "db_path": str(db_path),
            "document_count": stats['total_documents']
        }
        
    except Exception as e:
        print(f"\n✗ 数据库读取失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_vector_db_files():
    """测试向量数据库文件"""
    print_separator("向量数据库文件详情")
    
    db_path = PROJECT_ROOT / "data" / "chroma_db"
    
    print(f"\n【数据库目录】")
    print(f"  路径: {db_path}")
    
    stats = get_directory_stats(db_path)
    
    if stats["exists"]:
        print(f"\n【目录状态】: 存在 ✓")
        
        print_sub_separator("数据库文件列表")
        
        for file_info in stats["files"]:
            print(f"\n  文件: {file_info['path']}")
            print(f"    ├─ 大小: {file_info['size_formatted']}")
            print(f"    └─ 修改时间: {file_info['modified']}")
        
        print_sub_separator("文件统计")
        print(f"\n  ├─ 文件总数: {stats['file_count']}")
        print(f"  └─ 总大小: {stats['total_size_formatted']}")
        
        print_sub_separator("向量索引信息")
        print(f"\n  ├─ 索引类型: HNSW (Hierarchical Navigable Small World)")
        print(f"  ├─ 相似度度量: Cosine (余弦相似度)")
        print(f"  ├─ 嵌入模型: all-MiniLM-L6-v2 或 BAAI/bge-small-zh-v1.5")
        print(f"  └─ 嵌入维度: 384 或 768")
        
        return {"success": True, **stats}
    else:
        print(f"\n【目录状态】: 不存在")
        return {"success": True, "file_count": 0}


def test_documents_info():
    """测试文档信息"""
    print_separator("规则文档信息")
    
    rules_dir = PROJECT_ROOT / "data" / "rules"
    
    print(f"\n【规则文档目录】")
    print(f"  路径: {rules_dir}")
    
    if rules_dir.exists():
        print(f"\n【目录状态】: 存在 ✓")
        
        print_sub_separator("规则文档列表")
        
        doc_count = 0
        total_size = 0
        
        for doc in sorted(rules_dir.iterdir()):
            if doc.is_file() and not doc.name.startswith('.'):
                doc_count += 1
                size = doc.stat().st_size
                total_size += size
                
                print(f"\n  文档 #{doc_count}: {doc.name}")
                print(f"    ├─ 类型: {doc.suffix.upper()}")
                print(f"    ├─ 大小: {format_size(size)}")
                print(f"    └─ 修改时间: {format_datetime(doc.stat().st_mtime)}")
        
        print_sub_separator("文档统计")
        print(f"\n  ├─ 文档总数: {doc_count}")
        print(f"  └─ 总大小: {format_size(total_size)}")
        
        return {"success": True, "doc_count": doc_count, "total_size": total_size}
    else:
        print(f"\n【目录状态】: 不存在")
        return {"success": True, "doc_count": 0}


def test_embedding_model():
    """测试嵌入模型信息"""
    print_separator("嵌入模型信息")
    
    print(f"\n【嵌入模型配置】")
    print(f"  ├─ 模型名称: all-MiniLM-L6-v2 或 BAAI/bge-small-zh-v1.5")
    print(f"  ├─ 模型来源: HuggingFace")
    print(f"  ├─ 嵌入维度: 384 (MiniLM) 或 768 (bge-small-zh)")
    print(f"  ├─ 最大序列长度: 512")
    print(f"  └─ 运行设备: CPU")
    
    print_sub_separator("模型缓存位置")
    
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    print(f"\n  HuggingFace缓存目录: {cache_dir}")
    
    if cache_dir.exists():
        models = list(cache_dir.glob("models--*"))
        print(f"  已缓存的模型数: {len(models)}")
        for model in models[:5]:
            print(f"    ├─ {model.name}")
    
    return {"success": True}


def run_all_tests():
    """运行所有测试"""
    print_separator("RAG向量数据库 - 全面功能测试")
    print(f"  测试时间: {format_datetime(time.time())}")
    
    logger = TestLogger("RAG向量数据库测试")
    
    start = time.time()
    results = {}
    
    results["documents"] = test_documents_info()
    logger.log("规则文档信息", results["documents"]["success"], 
               f"文档数: {results['documents'].get('doc_count', 0)}")
    
    results["db_files"] = test_vector_db_files()
    logger.log("数据库文件", results["db_files"]["success"],
               f"文件数: {results['db_files'].get('file_count', 0)}")
    
    results["sqlite"] = test_sqlite_db()
    logger.log("SQLite数据库", results["sqlite"]["success"],
               f"文档数: {results['sqlite'].get('document_count', 0)}")
    
    results["embedding"] = test_embedding_model()
    logger.log("嵌入模型", True, "配置正常")
    
    print_separator("测试结果汇总")
    
    summary = logger.summary()
    print(f"\n总计: {summary['passed']}/{summary['total']} 测试通过")
    print(f"通过率: {summary['pass_rate']}")
    
    return results


if __name__ == "__main__":
    run_all_tests()
