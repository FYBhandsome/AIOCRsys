#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Chroma 数据库检索测试
通过 API 方式检索并打印 Chroma 数据库中的信息
"""
import httpx
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://127.0.0.1:8010"
TIMEOUT = 30.0


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def get_vector_db_stats():
    """获取向量数据库统计信息"""
    print_separator("Chroma 数据库统计信息")
    
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        response = client.get("/api/v1/vector-db/stats")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n  数据库路径: {data.get('db_path', 'N/A')}")
            print(f"  存在状态: {'✅ 存在' if data.get('exists') else '❌ 不存在'}")
            print(f"  文档总数: {data.get('total_documents', 0)}")
            print(f"  数据库大小: {data.get('db_size_formatted', 'N/A')}")
            print(f"  最后修改: {data.get('last_modified', 'N/A')}")
            
            collections = data.get('collections', [])
            print(f"\n  集合列表 ({len(collections)} 个):")
            for coll in collections:
                print(f"    - ID: {coll.get('id', 'N/A')}")
                print(f"      名称: {coll.get('name', 'N/A')}")
            
            return data
        else:
            print(f"  ❌ 获取失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return None


def search_documents(query: str, top_k: int = 5):
    """通过对话 API 搜索文档"""
    print_separator(f"检索测试: {query}")
    
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        start_time = time.time()
        response = client.post(
            "/api/v1/chat",
            json={"message": query}
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('data', {})
            
            print(f"\n  问题: {result.get('question', query)}")
            print(f"\n  回答:")
            print("-" * 70)
            answer = result.get('answer', '无回答')
            # 打印回答，每行不超过70字符
            for i in range(0, len(answer), 70):
                print(f"  {answer[i:i+70]}")
            print("-" * 70)
            print(f"\n  响应时间: {duration:.2f} 秒")
            print(f"  是否缓存: {result.get('cached', False)}")
            print(f"  时间戳: {result.get('timestamp', 'N/A')}")
            
            return result
        else:
            print(f"  ❌ 检索失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return None


def run_comprehensive_test():
    """运行综合测试"""
    print("\n" + "#" * 70)
    print("#  RAG Chroma 数据库检索测试")
    print(f"#  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 70)
    
    # 1. 获取数据库统计信息
    stats = get_vector_db_stats()
    
    if not stats or not stats.get('exists'):
        print("\n  ❌ 数据库不存在，无法继续测试")
        return False
    
    # 2. 测试检索功能
    test_queries = [
        "电赛国赛一等奖加多少分？",
        "英语六级证书加分规则",
        "省级竞赛获奖加分标准",
        "创新创业竞赛加分",
        "学科竞赛A类有哪些？"
    ]
    
    results = []
    for query in test_queries:
        result = search_documents(query)
        if result:
            results.append({
                'query': query,
                'success': True,
                'answer_length': len(result.get('answer', ''))
            })
        else:
            results.append({
                'query': query,
                'success': False,
                'answer_length': 0
            })
        time.sleep(0.5)  # 避免请求过快
    
    # 3. 打印测试汇总
    print_separator("测试结果汇总")
    
    print("\n  检索测试结果:")
    print("  " + "-" * 60)
    print(f"  {'查询内容':<30} {'状态':<10} {'回答长度':<10}")
    print("  " + "-" * 60)
    
    for r in results:
        status = "✅ 成功" if r['success'] else "❌ 失败"
        query_short = r['query'][:28] + "..." if len(r['query']) > 30 else r['query']
        print(f"  {query_short:<30} {status:<10} {r['answer_length']:<10}")
    
    print("  " + "-" * 60)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n  总计: {success_count}/{len(results)} 检索成功")
    
    print_separator("测试完成")
    
    return success_count == len(results)


if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
