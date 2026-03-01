#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断RAG路由加载问题"""
import sys
import os
import traceback

os.chdir(r"D:\PaddleOCR\PaddleOCRRAG")
sys.path.insert(0, r"D:\PaddleOCR")

print("=" * 60)
print("RAG路由加载诊断")
print("=" * 60)

print("\n[1] 测试导入routes模块...")
try:
    from app.api import routes
    print("  [OK] routes模块导入成功")
except Exception as e:
    print(f"  [FAIL] routes模块导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n[2] 检查api_router...")
try:
    router = routes.api_router
    print(f"  [OK] api_router存在，路由数: {len(router.routes)}")
except Exception as e:
    print(f"  [FAIL] api_router检查失败: {e}")
    traceback.print_exc()

print("\n[3] 测试get_api_router函数...")
try:
    api_router = routes.get_api_router()
    print(f"  [OK] get_api_router()成功，路由数: {len(api_router.routes)}")
except Exception as e:
    print(f"  [FAIL] get_api_router()失败: {e}")
    traceback.print_exc()

print("\n[4] 检查各路由模块...")
modules = [
    "certificate_routes",
    "chat_routes", 
    "document_routes",
    "system_routes",
    "prompt_routes",
    "vector_db_routes",
    "log_routes",
    "cache_routes"
]

for mod in modules:
    try:
        full_mod = f"app.api.{mod}"
        m = __import__(full_mod, fromlist=["router"])
        r = getattr(m, "router")
        print(f"  [OK] {mod}: {len(r.routes)} 条路由")
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
