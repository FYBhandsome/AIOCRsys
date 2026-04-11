#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除单例缓存并重建向量数据库
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 清除单例缓存
def clear_singleton_cache():
    """清除所有单例缓存"""
    from app.rag.vector_db.vector_db import RuleVectorDB
    from app.rag.vector_db.base_vector_db import BaseVectorDB
    
    # 清除 RuleVectorDB 单例
    RuleVectorDB._instances.clear()
    print("已清除 RuleVectorDB 单例缓存")
    
    # 清除 BaseVectorDB 缓存
    BaseVectorDB._initialized_collections.clear()
    BaseVectorDB._embedding_func_cache = None
    print("已清除 BaseVectorDB 缓存")

def rebuild_database():
    """重建数据库"""
    import chromadb
    from chromadb.config import Settings
    
    db_path = Path(r'd:\AIOCR\PaddleOCRRAG\data\chroma_db')
    
    # 删除旧数据库
    if db_path.exists():
        backup_dir = db_path.parent / f"chroma_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"备份到: {backup_dir}")
        shutil.copytree(db_path, backup_dir)
        shutil.rmtree(db_path)
        print("已删除旧数据库")
    
    # 创建新数据库
    db_path.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_or_create_collection(
        name="zongce_rules",
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"数据库已重建: {collection.name}")
    return client, collection

def import_documents(client, collection):
    """导入文档"""
    from app.rag import get_enhanced_rule_loader

    EnhancedRuleLoader, _ = get_enhanced_rule_loader()
    rules_dir = Path(r'd:\AIOCR\PaddleOCRRAG\data\rules')
    loader = EnhancedRuleLoader()
    
    documents = []
    
    # 加载所有规则文档
    for file_path in rules_dir.glob("*.md"):
        try:
            docs = loader.load_markdown(str(file_path))
            documents.extend(docs)
            print(f"加载: {file_path.name} ({len(docs)} 个文档)")
        except Exception as e:
            print(f"加载失败 {file_path.name}: {e}")
    
    if not documents:
        print("没有文档可导入")
        return
    
    # 添加到向量数据库
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]
    ids = [f"doc_{i}" for i in range(len(documents))]
    
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"已导入 {len(documents)} 个文档")

if __name__ == "__main__":
    print("=" * 60)
    print("清除缓存并重建向量数据库")
    print("=" * 60)
    
    # 添加项目路径
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # 1. 清除单例缓存
    print("\n[1/3] 清除单例缓存...")
    clear_singleton_cache()
    
    # 2. 重建数据库
    print("\n[2/3] 重建数据库...")
    client, collection = rebuild_database()
    
    # 3. 导入文档
    print("\n[3/3] 导入文档...")
    import_documents(client, collection)
    
    # 4. 验证
    print("\n[验证] 测试查询...")
    results = collection.query(
        query_texts=["学科竞赛"],
        n_results=3
    )
    
    print(f"查询成功: {len(results['documents'][0])} 个结果")
    for i, doc in enumerate(results['documents'][0]):
        print(f"  {i+1}. {doc[:100]}...")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 数据库重建完成!")
    print("=" * 60)
