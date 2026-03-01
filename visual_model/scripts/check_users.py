#!/usr/bin/env python3
import sqlite3
import os

db_path = "D:/PaddleOCR/visual_model/data/database.db"

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 60)
print("数据库中的用户列表")
print("=" * 60)

cursor.execute('SELECT * FROM users LIMIT 1')
sample = cursor.fetchone()
if sample:
    cursor.execute('PRAGMA table_info(users)')
    columns = cursor.fetchall()
    print("表结构:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    print()
    
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    col_names = [desc[1] for desc in columns]
    
    for u in users:
        print("-" * 40)
        for i, name in enumerate(col_names):
            if i < len(u):
                print(f"  {name}: {u[i]}")
        print()
else:
    print("数据库中没有用户")

conn.close()
