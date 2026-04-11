#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 ChromaDB max_seq_id 表问题
解决 "object of type 'int' has no len()" 错误

问题原因：
  max_seq_id 表中的 seq_id 列存储的是 INTEGER 类型，
  但 ChromaDB 的 _decode_seq_id 函数期望它是 BLOB 类型（8字节二进制数据）
  
解决方案：
  1. 将 INTEGER 类型的 seq_id 转换为 BLOB 类型
  2. 或者清空 max_seq_id 表，让 ChromaDB 重新初始化
"""
import sqlite3
import struct
import os
import shutil
from pathlib import Path
from datetime import datetime


def backup_database(db_path: str) -> str:
    """备份数据库"""
    backup_dir = Path(db_path).parent.parent / "chroma_db_backup_seq"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"chroma_backup_{timestamp}"
    
    try:
        db_dir = Path(db_path).parent
        shutil.copytree(db_dir, backup_path)
        print(f"[OK] 数据库已备份到: {backup_path}")
        return str(backup_path)
    except Exception as e:
        print(f"[ERROR] 备份失败: {e}")
        return None


def diagnose_max_seq_id(db_path: str):
    """诊断 max_seq_id 表"""
    print("=" * 60)
    print("诊断 max_seq_id 表")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表结构
    print("\n[表结构]")
    cursor.execute("PRAGMA table_info(max_seq_id)")
    for col in cursor.fetchall():
        print(f"  {col}")
    
    # 检查数据
    print("\n[数据]")
    cursor.execute("SELECT * FROM max_seq_id")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  segment_id: {row[0]}")
        print(f"  seq_id: {row[1]}")
        print(f"  seq_id type: {type(row[1])}")
        if isinstance(row[1], int):
            print(f"  [问题] seq_id 是整数类型，应该是 BLOB")
    
    conn.close()
    print("\n" + "=" * 60)
    return rows


def fix_max_seq_id(db_path: str):
    """修复 max_seq_id 表"""
    print("=" * 60)
    print("修复 max_seq_id 表")
    print("=" * 60)
    
    # 备份
    backup_path = backup_database(db_path)
    if backup_path is None:
        print("[WARN] 备份失败，是否继续? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取当前数据
        cursor.execute("SELECT segment_id, seq_id FROM max_seq_id")
        rows = cursor.fetchall()
        
        if not rows:
            print("[INFO] max_seq_id 表为空，无需修复")
            conn.close()
            return True
        
        print(f"\n[INFO] 发现 {len(rows)} 条记录需要修复")
        
        # 方法1: 清空 max_seq_id 表，让 ChromaDB 重新初始化
        print("\n[修复] 清空 max_seq_id 表...")
        cursor.execute("DELETE FROM max_seq_id")
        
        conn.commit()
        print("[OK] max_seq_id 表已清空")
        
        # 验证
        cursor.execute("SELECT COUNT(*) FROM max_seq_id")
        count = cursor.fetchone()[0]
        print(f"[验证] max_seq_id 表现在有 {count} 条记录")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 修复失败: {e}")
        conn.rollback()
        conn.close()
        return False


def int_to_blob(seq_id: int) -> bytes:
    """将整数转换为 8 字节 BLOB"""
    return struct.pack('>Q', seq_id)


def fix_max_seq_id_with_conversion(db_path: str):
    """修复 max_seq_id 表（保留数据，转换类型）"""
    print("=" * 60)
    print("修复 max_seq_id 表（转换类型）")
    print("=" * 60)
    
    # 备份
    backup_path = backup_database(db_path)
    if backup_path is None:
        print("[WARN] 备份失败，是否继续? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取当前数据
        cursor.execute("SELECT segment_id, seq_id FROM max_seq_id")
        rows = cursor.fetchall()
        
        if not rows:
            print("[INFO] max_seq_id 表为空，无需修复")
            conn.close()
            return True
        
        print(f"\n[INFO] 发现 {len(rows)} 条记录需要修复")
        
        # 创建临时表
        print("\n[修复] 创建临时表...")
        cursor.execute("""
            CREATE TABLE max_seq_id_new (
                segment_id TEXT PRIMARY KEY,
                seq_id BLOB NOT NULL
            )
        """)
        
        # 转换并插入数据
        print("[修复] 转换数据...")
        for segment_id, seq_id in rows:
            if isinstance(seq_id, int):
                # 将整数转换为 8 字节 BLOB
                blob_data = int_to_blob(seq_id)
            else:
                blob_data = seq_id
            
            cursor.execute(
                "INSERT INTO max_seq_id_new (segment_id, seq_id) VALUES (?, ?)",
                (segment_id, blob_data)
            )
            print(f"  {segment_id[:8]}... : {seq_id} -> {blob_data.hex()}")
        
        # 删除旧表
        print("[修复] 替换表...")
        cursor.execute("DROP TABLE max_seq_id")
        cursor.execute("ALTER TABLE max_seq_id_new RENAME TO max_seq_id")
        
        conn.commit()
        print("[OK] max_seq_id 表已修复")
        
        # 验证
        cursor.execute("SELECT segment_id, seq_id FROM max_seq_id")
        for row in cursor.fetchall():
            print(f"[验证] segment_id={row[0][:8]}..., seq_id={row[1].hex() if isinstance(row[1], bytes) else row[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False


def main():
    """主函数"""
    import sys
    
    db_path = r"d:\AIOCR\PaddleOCRRAG\data\chroma_db\chroma.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return 1
    
    print("ChromaDB max_seq_id 修复工具")
    print("=" * 60)
    print("1. 诊断 max_seq_id 表")
    print("2. 清空 max_seq_id 表（推荐）")
    print("3. 转换 seq_id 类型（保留数据）")
    print("4. 退出")
    print("=" * 60)
    
    choice = input("\n请选择操作 (1-4): ").strip()
    
    if choice == "1":
        diagnose_max_seq_id(db_path)
    elif choice == "2":
        if fix_max_seq_id(db_path):
            print("\n[SUCCESS] 修复成功！请重启 RAG 服务验证。")
            return 0
        return 1
    elif choice == "3":
        if fix_max_seq_id_with_conversion(db_path):
            print("\n[SUCCESS] 修复成功！请重启 RAG 服务验证。")
            return 0
        return 1
    elif choice == "4":
        print("退出")
        return 0
    else:
        print("无效选择")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
