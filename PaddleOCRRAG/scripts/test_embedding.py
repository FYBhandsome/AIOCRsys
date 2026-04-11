#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试嵌入模型加载
验证HF镜像配置是否生效
"""
import os
import time

print('=' * 60)
print('嵌入模型加载测试 (使用HF镜像)')
print('=' * 60)

# 设置HF镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
print(f'\n[配置] HF_ENDPOINT = {os.environ.get("HF_ENDPOINT")}')

# 测试加载
print('\n[测试] 加载嵌入模型...')
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    
    start = time.time()
    ef = SentenceTransformerEmbeddingFunction(
        model_name='all-MiniLM-L6-v2',
        device='cpu'
    )
    load_time = time.time() - start
    print(f'  状态: 加载成功')
    print(f'  加载时间: {load_time:.2f}秒')
    
    # 测试嵌入
    print('\n[测试] 执行嵌入测试...')
    test_text = '这是一个测试文本'
    start = time.time()
    embedding = ef([test_text])
    embed_time = time.time() - start
    print(f'  输入文本: {test_text}')
    print(f'  嵌入维度: {len(embedding[0])}')
    print(f'  嵌入时间: {embed_time:.4f}秒')
    print('  状态: 成功')
    
except Exception as e:
    print(f'  状态: 失败')
    print(f'  错误: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '=' * 60)
