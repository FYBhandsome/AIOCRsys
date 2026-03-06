#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移certificates表和certificate_images表
"""
import asyncio
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from config import settings

async def migrate_certificates_tables():
    """迁移certificates表和certificate_images表"""
    print("开始迁移certificates表和certificate_images表...")
    
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models"]}
    )
    
    try:
        conn = Tortoise.get_connection("default")
        
        print("检查certificates表...")
        
        # 检查表是否存在
        tables = await conn.execute_query_dict(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [t['name'] for t in tables]
        
        if 'certificates' in table_names:
            print("  certificates表存在，需要更新结构")
            
            # 重命名旧表
            await conn.execute_query("ALTER TABLE certificates RENAME TO certificates_old")
            print("  已重命名旧表为certificates_old")
            
            # 创建新表
            await Tortoise.generate_schemas(safe=True)
            print("  已创建新的certificates表和certificate_images表")
            
            print("✓ certificates表和certificate_images表迁移完成！")
        else:
            print("  certificates表不存在，创建新表")
            await Tortoise.generate_schemas(safe=True)
            print("✓ certificates表和certificate_images表创建完成！")
        
        return True
        
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(migrate_certificates_tables())
