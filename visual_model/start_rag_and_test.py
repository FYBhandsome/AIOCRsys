#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动RAG服务并运行端到端测试
"""
import subprocess
import sys
import time
import asyncio
import httpx

async def test_rag_service():
    """测试RAG服务"""
    print("=" * 60)
    print("测试RAG服务连接")
    print("=" * 60)
    
    # 先测试健康检查
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("\n1. 测试健康检查端点...")
            response = await client.get("http://localhost:8010/api/v1/system/health")
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"   响应: {response.json()}")
                print("   ✅ 健康检查通过")
            else:
                print(f"   响应: {response.text}")
                return False
            
            # 测试聊天接口
            print("\n2. 测试聊天接口...")
            response = await client.post(
                "http://localhost:8010/api/v1/chat",
                json={
                    "message": "你好",
                    "use_rag": False,
                    "chat_history": []
                },
                timeout=30.0
            )
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"   响应: {response.json()}")
                print("   ✅ 聊天接口测试成功")
            else:
                print(f"   响应: {response.text}")
            
            # 测试加分计算接口
            print("\n3. 测试加分计算接口...")
            response = await client.post(
                "http://localhost:8010/api/v1/certificate/calculate",
                json={
                    "certificate_text": "蓝桥杯全国软件和信息技术专业人才大赛 省级一等奖",
                    "student_info": {"user_id": "test_e2e", "student_id": "202300502101"}
                },
                timeout=30.0
            )
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"   响应: {response.json()}")
                print("   ✅ 加分计算接口测试成功")
            else:
                print(f"   响应: {response.text}")
            
            print("\n" + "=" * 60)
            print("测试完成")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("请确保RAG服务已在端口8010上启动！")
    print("如果没有启动，请在另一个终端运行:")
    print("  cd d:\\PaddleOCR\\PaddleOCRRAG")
    print("  uvicorn app.main:app --host 127.0.0.1 --port 8010")
    print("\n按Enter键继续测试...")
    input()
    
    # 测试服务
    result = asyncio.run(test_rag_service())
    
    if result:
        print("\n✅ RAG服务测试通过！现在运行pytest测试...")
        # 运行pytest
        import subprocess
        subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/test_rag_integration.py::TestRAGIntegrationE2E",
            "-v", "--tb=short"
        ])
    else:
        print("\n❌ RAG服务测试失败！请检查服务是否正常运行。")

if __name__ == "__main__":
    main()
