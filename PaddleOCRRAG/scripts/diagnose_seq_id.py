#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断 ChromaDB 序列ID问题"""
import sqlite3

db_path = r'd:\AIOCR\PaddleOCRRAG\data\chroma_db\chroma.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('=' * 60)
print('检查所有表结构')
print('=' * 60)

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'所有表: {[t[0] for t in tables]}')

for table in tables:
    table_name = table[0]
    print(f'\n[{table_name} 表结构]')
    cursor.execute(f'PRAGMA table_info({table_name})')
    for col in cursor.fetchall():
        print(f'  {col}')

# 检查是否有 seq_id 相关的问题
print('\n' + '=' * 60)
print('检查 seq_id 相关问题')
print('=' * 60)

# 检查 embedding_fulltext_search
try:
    cursor.execute("PRAGMA table_info(embedding_fulltext_search)")
    cols = cursor.fetchall()
    col_names = [col[1] for col in cols]
    print(f'\nembedding_fulltext_search 列: {col_names}')
    
    if 'seq_id' in col_names:
        cursor.execute("SELECT seq_id, typeof(seq_id) FROM embedding_fulltext_search LIMIT 5")
        for row in cursor.fetchall():
            print(f'  seq_id={row[0]}, type={row[1]}')
except Exception as e:
    print(f'错误: {e}')

conn.close()
print('\n' + '=' * 60)
