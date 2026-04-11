#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彻底重建ChromaDB数据库
解决 'table segments already exists' 和 'dict object has no attribute dimensionality' 错误
"""
import os
import sys
import shutil
import sqlite3
from pathlib import Path

db_path = Path(r'd:\AIOCR\PaddleOCRRAG\data\chroma_db')
db_file = db_path / 'chroma.sqlite3'

print("=" * 60)
print("彻底重建ChromaDB数据库")
print("=" * 60)

if db_file.exists():
    print(f"\n检查数据库文件: {db_file}")
    
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"现有表: {[t[0] for t in tables]}")
        
        cursor.execute("SELECT id, name FROM collections")
        collections = cursor.fetchall()
        print(f"现有集合: {collections}")
        
        conn.close()
    except Exception as e:
        print(f"检查数据库失败: {e}")

print("\n步骤1: 完全删除数据库目录...")
if db_path.exists():
    try:
        shutil.rmtree(db_path)
        print("数据库目录已删除")
    except Exception as e:
        print(f"删除失败: {e}")
        os.makedirs(db_path, exist_ok=True)
        if db_file.exists():
            os.remove(db_file)
            print("数据库文件已删除")

print("\n步骤2: 创建新的数据库目录...")
os.makedirs(db_path, exist_ok=True)
print(f"目录已创建: {db_path}")

print("\n步骤3: 初始化新数据库...")
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path=str(db_path),
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_or_create_collection(
    name="zongce_rules",
    metadata={"hnsw:space": "cosine"}
)

print(f"集合已创建: zongce_rules")
print(f"当前文档数: {collection.count()}")

print("\n步骤4: 导入规则文档...")
rules_dir = Path(r'd:\AIOCR\PaddleOCRRAG\data\rules')
documents = []
metadatas = []

docx_file = rules_dir / "03、计算机学院综合测评实施细则（2025）.docx"
if docx_file.exists():
    print(f"\n正在读取: {docx_file.name}")
    try:
        import docx2txt
        text = docx2txt.process(str(docx_file))
        chunks = text.split('\n\n')
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:
                documents.append(chunk.strip())
                metadatas.append({
                    "source": docx_file.name,
                    "chunk_id": i,
                    "type": "rules"
                })
        print(f"  提取了 {len(documents)} 个文档块")
    except Exception as e:
        print(f"  读取失败: {e}")

excel_file = rules_dir / "05、学科竞赛名称列表.xlsx"
if excel_file.exists():
    print(f"\n正在读取: {excel_file.name}")
    try:
        import pandas as pd
        df = pd.read_excel(excel_file)
        start_idx = len(documents)
        for idx, row in df.iterrows():
            text = ' '.join([str(v) for v in row.values if pd.notna(v)])
            if len(text.strip()) > 20:
                documents.append(text.strip())
                metadatas.append({
                    "source": excel_file.name,
                    "row_id": idx,
                    "type": "competition_list"
                })
        print(f"  提取了 {len(documents) - start_idx} 个文档块")
    except Exception as e:
        print(f"  读取失败: {e}")

if documents:
    print(f"\n正在导入 {len(documents)} 个文档块...")
    ids = [f"doc_{i}" for i in range(len(documents))]
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"导入完成!")
    print(f"当前文档数: {collection.count()}")

print("\n步骤5: 验证查询...")
results = collection.query(
    query_texts=["学科竞赛"],
    n_results=3
)

print(f"查询结果: {len(results['documents'][0])} 个文档")
for i, doc in enumerate(results['documents'][0]):
    print(f"  {i+1}. {doc[:80]}...")

print("\n" + "=" * 60)
print("[SUCCESS] 数据库重建完成!")
print("=" * 60)
