#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAG服务启动测试脚本

注意: 此测试需要 langchain，在 Windows 环境下可能因 numpy/transformers 
兼容性问题而崩溃。设置环境变量 SKIP_LANGCHAIN_TESTS=1 可跳过此测试。
"""
import sys
import os
from pathlib import Path
import traceback
import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.skip_if_no_langchain
def test_init():
    """测试初始化"""
    print("=" * 60)
    print("测试RAG服务初始化")
    print("=" * 60)
    
    try:
        print("\n1. 测试导入模块...")
        from app.api.routes import init_optimized_components
        print("   ✓ 模块导入成功")
        
        print("\n2. 测试初始化组件...")
        result = init_optimized_components()
        print(f"   初始化结果: {result}")
        
        if result:
            print("\n3. 测试FastAPI应用...")
            from app.main import app
            print(f"   ✓ FastAPI应用创建成功: {app.title}")
            
            print("\n4. 测试向量数据库...")
            from app.rag.vector_db.vector_db import get_vector_db
            vdb = get_vector_db()
            print(f"   ✓ 向量数据库连接成功: {vdb.collection_name}")
            print(f"   文档数量: {vdb.collection.count()}")
            
            print("\n" + "=" * 60)
            print("所有测试通过！RAG服务可以正常启动")
            print("=" * 60)
        else:
            print("\n初始化失败，请检查日志")
            
    except Exception as e:
        print(f"\n错误: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    test_init()
