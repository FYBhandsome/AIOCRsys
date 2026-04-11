#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check database table structure"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def check_db():
    from tortoise import Tortoise
    from config import settings

    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models"]}
    )

    try:
        conn = Tortoise.get_connection("default")
        
        # Check if comprehensive_scores table exists and get columns
        if "sqlite" in settings.DATABASE_URL.lower():
            rows = await conn.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='comprehensive_scores'"
            )
            if rows:
                print("Table 'comprehensive_scores' exists")
                
                # Get column info
                columns = await conn.execute_query("PRAGMA table_info(comprehensive_scores)")
                print("\nColumns in comprehensive_scores table:")
                for col in columns[1]:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("Table 'comprehensive_scores' does NOT exist")
        else:
            # For other databases
            columns = await conn.execute_query(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'comprehensive_scores'"
            )
            print("\nColumns in comprehensive_scores table:")
            for col in columns[1]:
                print(f"  - {col[0]}")

    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check_db())
