#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 确保使用 venv 中的包
venv_lib = Path(__file__).parent / "venv" / "Lib" / "site-packages"
if venv_lib.exists():
    sys.path.insert(0, str(venv_lib))

from aerich import Command
from config import TORTOISE_ORM

async def main():
    print("="*80)
    print("数据库迁移工具")
    print("="*80)
    
    # 初始化 aerich command
    command = Command(tortoise_config=TORTOISE_ORM, location="./migrations", app="models")
    
    # 初始化
    print("\n初始化 aerich...")
    await command.init()
    print("[OK] 初始化完成")
    
    # 生成迁移文件
    print("\n生成迁移文件...")
    try:
        migration_name = await command.migrate(name="update_models")
        print(f"[OK] 迁移文件生成成功: {migration_name}")
    except Exception as e:
        print(f"[ERROR] 生成迁移文件失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 应用迁移
    print("\n应用迁移...")
    try:
        await command.upgrade()
        print("[OK] 迁移应用成功")
    except Exception as e:
        print(f"[ERROR] 应用迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*80)
    print("数据库迁移完成！")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
