#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 ChromaDB 查询"""
import chromadb
from chromadb.config import Settings

print('Testing ChromaDB query...')

# 创建客户端
client = chromadb.PersistentClient(
    path=r'd:\AIOCR\PaddleOCRRAG\data\chroma_db',
    settings=Settings(anonymized_telemetry=False)
)

# 获取集合
collection = client.get_collection('zongce_rules')
print(f'Collection: {collection.name}')
print(f'Count: {collection.count()}')
print(f'Metadata: {collection.metadata}')

# 测试查询
try:
    results = collection.query(
        query_texts=['测试查询'],
        n_results=3
    )
    print(f'\nQuery successful!')
    print(f'Documents count: {len(results["documents"][0])}')
    for i, doc in enumerate(results["documents"][0]):
        print(f'  Doc {i+1}: {doc[:100]}...')
except Exception as e:
    print(f'\nQuery failed: {e}')
    import traceback
    traceback.print_exc()
