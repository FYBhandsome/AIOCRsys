#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复迁移文件格式
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
    print("修复迁移文件格式")
    print("="*80)
    
    # 初始化 aerich command
    command = Command(tortoise_config=TORTOISE_ORM, location="./migrations", app="models")
    
    # 修复迁移文件
    print("\n修复迁移文件...")
    try:
        await command.fix_migrations()
        print("[OK] 迁移文件修复成功")
    except Exception as e:
        print(f"[ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*80)
    print("修复完成！")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
