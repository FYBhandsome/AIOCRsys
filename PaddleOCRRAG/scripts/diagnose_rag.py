#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统诊断和测试脚本
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

def log_info(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [INFO] {message}")

def log_error(message):
    """打印错误日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [ERROR] {message}")

def log_warn(message):
    """打印警告日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [WARN] {message}")

def test_dependencies():
    """测试依赖库"""
    log_info("=" * 60)
    log_info("测试依赖库")
    log_info("=" * 60)
    
    dependencies = [
        ("chromadb", "ChromaDB向量数据库"),
        ("sentence_transformers", "Sentence Transformers嵌入模型"),
        ("langchain", "LangChain框架"),
        ("torch", "PyTorch深度学习框架"),
        ("transformers", "Transformers库"),
    ]
    
    results = {}
    for module_name, description in dependencies:
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "未知版本")
            log_info(f"✓ {description}: {module_name} v{version}")
            results[module_name] = {"status": "OK", "version": version}
        except ImportError as e:
            log_error(f"✗ {description}: {module_name} 未安装 - {e}")
            results[module_name] = {"status": "FAILED", "error": str(e)}
        except Exception as e:
            log_error(f"✗ {description}: {module_name} 加载失败 - {e}")
            results[module_name] = {"status": "ERROR", "error": str(e)}
    
    return results

def test_chromadb_connection():
    """测试ChromaDB连接"""
    log_info("=" * 60)
    log_info("测试ChromaDB连接")
    log_info("=" * 60)
    
    db_path = Path(__file__).parent.parent / "data" / "chroma_db"
    
    try:
        import chromadb
        
        log_info(f"数据库路径: {db_path}")
        log_info("正在创建ChromaDB客户端...")
        
        # 尝试使用EphemeralClient（内存模式）
        try:
            client = chromadb.EphemeralClient()
            log_info("✓ EphemeralClient创建成功（内存模式）")
        except Exception as e:
            log_warn(f"EphemeralClient失败: {e}")
        
        # 尝试使用PersistentClient
        try:
            client = chromadb.PersistentClient(path=str(db_path))
            log_info("✓ PersistentClient创建成功（持久化模式）")
            
            # 获取集合
            collections = client.list_collections()
            log_info(f"发现 {len(collections)} 个集合")
            
            for coll in collections:
                log_info(f"  - {coll.name}: {coll.count()} 条记录")
            
            return {"status": "OK", "collections": len(collections)}
            
        except Exception as e:
            log_error(f"PersistentClient失败: {e}")
            return {"status": "FAILED", "error": str(e)}
            
    except Exception as e:
        log_error(f"ChromaDB测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}

def test_sqlite_direct():
    """直接测试SQLite数据库"""
    log_info("=" * 60)
    log_info("测试SQLite直接访问")
    log_info("=" * 60)
    
    import sqlite3
    
    db_path = Path(__file__).parent.parent / "data" / "chroma_db" / "chroma.sqlite3"
    
    if not db_path.exists():
        log_error(f"数据库文件不存在: {db_path}")
        return {"status": "FAILED", "error": "数据库文件不存在"}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        log_info(f"发现 {len(tables)} 个表")
        
        # 获取集合
        cursor.execute("SELECT id, name FROM collections;")
        collections = cursor.fetchall()
        log_info(f"发现 {len(collections)} 个集合")
        
        for coll_id, coll_name in collections:
            log_info(f"  - {coll_name} (ID: {coll_id})")
        
        # 获取文档数量
        try:
            cursor.execute("SELECT COUNT(*) FROM embedding_fulltext_search;")
            count = cursor.fetchone()[0]
            log_info(f"总文档数: {count}")
        except Exception as e:
            log_warn(f"获取文档数失败: {e}")
            count = 0
        
        conn.close()
        log_info("✓ SQLite直接访问成功")
        return {"status": "OK", "tables": len(tables), "collections": len(collections), "documents": count}
        
    except Exception as e:
        log_error(f"SQLite测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}

def test_embedding_model():
    """测试嵌入模型"""
    log_info("=" * 60)
    log_info("测试嵌入模型")
    log_info("=" * 60)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model_name = "all-MiniLM-L6-v2"
        log_info(f"正在加载模型: {model_name}")
        
        start_time = time.time()
        model = SentenceTransformer(model_name)
        load_time = time.time() - start_time
        log_info(f"✓ 模型加载成功 (耗时: {load_time:.2f}秒)")
        
        # 测试编码
        test_text = "这是一个测试句子"
        start_time = time.time()
        embedding = model.encode(test_text)
        encode_time = time.time() - start_time
        
        log_info(f"✓ 编码测试成功")
        log_info(f"  - 输入: {test_text}")
        log_info(f"  - 向量维度: {len(embedding)}")
        log_info(f"  - 编码耗时: {encode_time*1000:.2f}ms")
        
        return {"status": "OK", "dimension": len(embedding), "load_time": load_time}
        
    except Exception as e:
        log_error(f"嵌入模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}

def test_vector_search():
    """测试向量检索"""
    log_info("=" * 60)
    log_info("测试向量检索功能")
    log_info("=" * 60)
    
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        db_path = Path(__file__).parent.parent / "data" / "chroma_db"
        
        log_info("初始化ChromaDB客户端...")
        client = chromadb.PersistentClient(path=str(db_path))
        
        log_info("加载嵌入模型...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # 获取集合
        collection = client.get_collection("zongce_rules")
        log_info(f"获取集合: zongce_rules ({collection.count()} 条记录)")
        
        # 测试查询
        test_queries = [
            "省级竞赛一等奖加多少分",
            "英语四级证书加分标准",
            "社会实践要求"
        ]
        
        for query in test_queries:
            log_info(f"\n查询: {query}")
            
            start_time = time.time()
            query_embedding = model.encode(query)
            encode_time = time.time() - start_time
            
            start_time = time.time()
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=3
            )
            search_time = time.time() - start_time
            
            log_info(f"  编码耗时: {encode_time*1000:.2f}ms")
            log_info(f"  检索耗时: {search_time*1000:.2f}ms")
            
            if results["documents"] and results["documents"][0]:
                for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
                    log_info(f"  结果{i+1}: [距离={dist:.4f}] {doc[:100]}...")
        
        log_info("\n✓ 向量检索测试成功")
        return {"status": "OK"}
        
    except Exception as e:
        log_error(f"向量检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}

def run_diagnostics():
    """运行所有诊断测试"""
    log_info("=" * 60)
    log_info("RAG系统诊断测试")
    log_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_info("=" * 60)
    
    results = {}
    
    results["dependencies"] = test_dependencies()
    results["sqlite"] = test_sqlite_direct()
    results["chromadb"] = test_chromadb_connection()
    results["embedding"] = test_embedding_model()
    results["vector_search"] = test_vector_search()
    
    log_info("=" * 60)
    log_info("测试结果汇总")
    log_info("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r.get("status") == "OK")
    
    for name, result in results.items():
        status = "✓ 通过" if result.get("status") == "OK" else "✗ 失败"
        log_info(f"  {status}: {name}")
    
    log_info(f"\n总计: {passed}/{total} 测试通过")
    log_info(f"通过率: {passed/total*100:.1f}%")
    
    return results

if __name__ == "__main__":
    run_diagnostics()
