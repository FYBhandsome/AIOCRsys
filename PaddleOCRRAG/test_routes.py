#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试路由加载"""
import sys
import traceback

print("开始测试路由加载...")

try:
    print("1. 测试 certificate_routes...")
    from app.api.certificate_routes import router as r1
    print("   certificate_routes OK")
except Exception as e:
    print(f"   certificate_routes FAILED: {e}")
    traceback.print_exc()

try:
    print("2. 测试 chat_routes...")
    from app.api.chat_routes import router as r2
    print("   chat_routes OK")
except Exception as e:
    print(f"   chat_routes FAILED: {e}")
    traceback.print_exc()

try:
    print("3. 测试 document_routes...")
    from app.api.document_routes import router as r3
    print("   document_routes OK")
except Exception as e:
    print(f"   document_routes FAILED: {e}")
    traceback.print_exc()

try:
    print("4. 测试 system_routes...")
    from app.api.system_routes import router as r4
    print("   system_routes OK")
except Exception as e:
    print(f"   system_routes FAILED: {e}")
    traceback.print_exc()

try:
    print("5. 测试 prompt_routes...")
    from app.api.prompt_routes import router as r5
    print("   prompt_routes OK")
except Exception as e:
    print(f"   prompt_routes FAILED: {e}")
    traceback.print_exc()

try:
    print("6. 测试 vector_db_routes...")
    from app.api.vector_db_routes import router as r6
    print("   vector_db_routes OK")
except Exception as e:
    print(f"   vector_db_routes FAILED: {e}")
    traceback.print_exc()

try:
    print("7. 测试 log_routes...")
    from app.api.log_routes import router as r7
    print("   log_routes OK")
except Exception as e:
    print(f"   log_routes FAILED: {e}")
    traceback.print_exc()

try:
    print("8. 测试 cache_routes...")
    from app.api.cache_routes import router as r8
    print("   cache_routes OK")
except Exception as e:
    print(f"   cache_routes FAILED: {e}")
    traceback.print_exc()

print("\n所有路由测试完成!")
