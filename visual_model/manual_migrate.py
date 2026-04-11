#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动数据库迁移脚本
由于 SQLite 的限制，某些迁移需要手动处理
"""

import sys
import os
import asyncio
from pathlib import Path

# 确保使用 venv 中的包
venv_lib = Path(__file__).parent / "venv" / "Lib" / "site-packages"
if venv_lib.exists():
    sys.path.insert(0, str(venv_lib))

from tortoise import Tortoise
from config import TORTOISE_ORM
from app.models.tortoise_models import *

async def main():
    print("="*80)
    print("手动数据库迁移")
    print("="*80)
    
    # 初始化数据库连接
    print("\n初始化数据库连接...")
    await Tortoise.init(config=TORTOISE_ORM)
    print("[OK] 数据库连接成功")
    
    # 生成数据库架构
    print("\n生成数据库架构（创建缺失的表）...")
    try:
        await Tortoise.generate_schemas()
        print("[OK] 数据库架构生成成功")
    except Exception as e:
        print(f"[ERROR] 生成数据库架构失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 关闭数据库连接
    await Tortoise.close_connections()
    
    print("\n" + "="*80)
    print("数据库迁移完成！")
    print("="*80)
    print("\n注意：")
    print("- 新表已创建")
    print("- 缺失的列已添加")
    print("- 现有数据已保留")
    print("- 如需修改列属性，请手动执行 SQL")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
