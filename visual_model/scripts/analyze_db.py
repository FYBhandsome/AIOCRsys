#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构分析脚本
"""
import sqlite3
import pandas as pd
import os

db_path = 'D:/PaddleOCR/visual_model/data/database.db'

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('=== 数据库表列表 ===')
for t in tables:
    print(f'  - {t[0]}')

# 获取每个表的结构
for table in tables:
    table_name = table[0]
    print(f'\n=== 表: {table_name} ===')
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f'  {col[1]:30} {col[2]:15} NULL={col[3]} DEFAULT={col[4]} PK={col[5]}')
    
    # 获取行数
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'  -- 总行数: {count} --')

conn.close()
