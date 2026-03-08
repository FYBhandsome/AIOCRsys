#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import httpx

async def test_rag_service():
    """测试RAG服务是否正常"""
    base_url = "http://localhost:8010"
    
    print("=" * 60)
    print("测试RAG服务连接")
    print("=" * 60)
    
    # 测试健康检查
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("\n1. 测试健康检查端点...")
            response = await client.get(f"{base_url}/api/v1/system/health")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            
            if response.status_code == 200:
                print("   ✅ 健康检查通过")
            else:
                print("   ❌ 健康检查失败")
                return False
            
            # 测试文档列表
            print("\n2. 测试文档列表端点...")
            try:
                response = await client.get(f"{base_url}/api/v1/documents")
                print(f"   状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"   响应: {response.json()}")
                    print("   ✅ 文档列表获取成功")
                else:
                    print(f"   响应: {response.text}")
            except Exception as e:
                print(f"   ⚠️ 文档列表测试失败: {e}")
            
            # 测试聊天接口
            print("\n3. 测试聊天接口...")
            try:
                response = await client.post(
                    f"{base_url}/api/v1/chat",
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
            except Exception as e:
                print(f"   ⚠️ 聊天接口测试失败: {e}")
            
            # 测试加分计算接口
            print("\n4. 测试加分计算接口...")
            try:
                response = await client.post(
                    f"{base_url}/api/v1/certificate/calculate",
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
            except Exception as e:
                print(f"   ⚠️ 加分计算接口测试失败: {e}")
            
            print("\n" + "=" * 60)
            print("测试完成")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_rag_service())
