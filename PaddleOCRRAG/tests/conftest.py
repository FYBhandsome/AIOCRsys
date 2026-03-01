#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest 配置文件
解决 Windows 环境下 numpy/transformers 兼容性问题
"""
import os
import sys
import pytest

# 在导入任何其他模块之前设置环境变量
# 禁用 numpy BLAS 检查，解决 Windows 下的崩溃问题
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')
os.environ.setdefault('NUMEXPR_NUM_THREADS', '1')

# 禁用 numpy 的 FPE 检查
os.environ.setdefault('NPY_DISABLE_CPU_FEATURES', 'AVX512F,AVX512CD,AVX512_SKX')

# 需要跳过的测试文件（因为它们导入了 langchain）
SKIP_TEST_FILES = [
    'test_category_aware_rag.py',
    'test_startup.py',
]


def pytest_configure(config):
    """Pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
    config.addinivalue_line(
        "markers", "skip_if_no_langchain: skip test if langchain is not available"
    )


def pytest_ignore_collect(collection_path, config):
    """忽略需要 langchain 的测试文件收集"""
    # 检查是否应该跳过 langchain 测试
    skip_langchain = os.environ.get('SKIP_LANGCHAIN_TESTS', '').lower() in ('1', 'true', 'yes')
    
    if skip_langchain:
        # 获取文件名
        file_name = os.path.basename(str(collection_path))
        if file_name in SKIP_TEST_FILES:
            return True  # 忽略此文件
    
    return False  # 不忽略
