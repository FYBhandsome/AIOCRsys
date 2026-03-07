#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构与模型定义验证脚本
检查数据库表结构与Tortoise ORM模型定义是否一致
"""
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple

DB_PATH = Path('D:/PaddleOCR/visual_model/data/database.db')


def get_db_tables() -> List[str]:
    """获取数据库中的所有表名"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_') and not row[0].startswith('aerich')]
    conn.close()
    return tables


def get_table_columns(table_name: str) -> Dict[str, Tuple[str, bool]]:
    """获取表的列信息 {列名: (类型, 是否NOT NULL)}"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {}
    for col in cursor.fetchall():
        col_name = col[1]
        col_type = col[2]
        not_null = bool(col[3])
        columns[col_name] = (col_type, not_null)
    conn.close()
    return columns


def get_table_indexes(table_name: str) -> List[str]:
    """获取表的索引"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = [row[1] for row in cursor.fetchall()]
    conn.close()
    return indexes


async def get_model_definitions() -> Dict[str, Dict]:
    """获取模型定义"""
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from tortoise import Tortoise
    from config import settings
    
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models"]}
    )
    
    models = {}
    for model_name, model in Tortoise.apps.get("models", {}).items():
        if model_name.startswith("_"):
            continue
            
        table = model._meta.db_table
        if table.startswith("aerich"):
            continue
            
        fields = {}
        for field_name, field in model._meta.fields_map.items():
            fields[field_name] = {
                "type": field.__class__.__name__,
                "nullable": field.null,
                "default": field.default is not None,
            }
        
        models[table] = {
            "model_name": model_name,
            "fields": fields,
        }
    
    await Tortoise.close_connections()
    return models


def compare_field_types(db_type: str, model_type: str) -> bool:
    """比较数据库类型和模型类型是否兼容"""
    type_mapping = {
        "CharField": ["VARCHAR", "TEXT", "CHAR"],
        "TextField": ["TEXT"],
        "IntField": ["INTEGER", "INT"],
        "FloatField": ["REAL", "FLOAT", "DOUBLE"],
        "BooleanField": ["BOOLEAN", "INTEGER", "INT"],
        "DatetimeField": ["TIMESTAMP", "DATETIME"],
        "DateField": ["DATE"],
        "JSONField": ["JSON", "TEXT"],
    }
    
    db_type_upper = db_type.upper()
    for model_t, db_types in type_mapping.items():
        if model_type == model_t:
            for db_t in db_types:
                if db_type_upper.startswith(db_t):
                    return True
    
    return False


def main():
    """主函数"""
    print("=" * 70)
    print("数据库结构与模型定义验证")
    print("=" * 70)
    
    # 获取数据库表
    db_tables = get_db_tables()
    print(f"\n数据库中的表 ({len(db_tables)}个):")
    for t in db_tables:
        print(f"  - {t}")
    
    # 获取模型定义
    print("\n正在获取模型定义...")
    models = asyncio.run(get_model_definitions())
    
    print(f"\n模型定义中的表 ({len(models)}个):")
    for table in models:
        print(f"  - {table}")
    
    # 比较差异
    print("\n" + "=" * 70)
    print("差异分析")
    print("=" * 70)
    
    db_tables_set = set(db_tables)
    model_tables_set = set(models.keys())
    
    # 数据库中有但模型中没有的表
    extra_tables = db_tables_set - model_tables_set
    if extra_tables:
        print(f"\n⚠️ 数据库中有但模型中没有的表 ({len(extra_tables)}个):")
        for t in extra_tables:
            print(f"  - {t}")
    
    # 模型中有但数据库中没有的表
    missing_tables = model_tables_set - db_tables_set
    if missing_tables:
        print(f"\n❌ 模型中有但数据库中没有的表 ({len(missing_tables)}个):")
        for t in missing_tables:
            print(f"  - {t}")
    
    # 检查字段差异
    common_tables = db_tables_set & model_tables_set
    
    all_match = True
    for table in sorted(common_tables):
        db_columns = get_table_columns(table)
        model_fields = models[table]["fields"]
        
        db_columns_set = set(db_columns.keys())
        model_fields_set = set(model_fields.keys())
        
        extra_columns = db_columns_set - model_fields_set - {"id"}  # id是自动添加的
        missing_columns = model_fields_set - db_columns_set - {"id"}
        
        if extra_columns or missing_columns:
            all_match = False
            print(f"\n📋 表 {table}:")
            if extra_columns:
                print(f"  ⚠️ 数据库中有但模型中没有的字段: {extra_columns}")
            if missing_columns:
                print(f"  ❌ 模型中有但数据库中没有的字段: {missing_columns}")
    
    # 检查索引
    print("\n" + "=" * 70)
    print("索引检查")
    print("=" * 70)
    
    for table in sorted(common_tables):
        indexes = get_table_indexes(table)
        if indexes:
            print(f"\n表 {table} 的索引:")
            for idx in indexes:
                print(f"  - {idx}")
    
    # 总结
    print("\n" + "=" * 70)
    print("验证结果")
    print("=" * 70)
    
    if all_match and not extra_tables and not missing_tables:
        print("\n✅ 数据库结构与模型定义完全匹配!")
    else:
        print("\n⚠️ 数据库结构与模型定义存在差异，请检查上述报告。")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
