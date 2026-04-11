#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试数学建模证书的RAG评分"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_math_modeling():
    from app.services.rag_client import get_rag_client
    from app.services.certificate_service import get_certificate_service

    rag_client = get_rag_client()
    cert_service = get_certificate_service()

    # 数学建模证书文本
    test_text = """全国大学生数学建模竞赛 获奖证书
北华航天工业学院
学生：樊意彬 魏泽琰 郭学森
指导教师：聂铭玮
荣获 2024年河北赛区本科组一等奖
河北省教育厅
中国工业与应用数学学会"""

    print("=" * 70)
    print("数学建模证书测试")
    print("=" * 70)
    print(f"\n证书文本:\n{test_text}\n")

    # 测试RAG直接调用
    print("[1] RAG服务直接调用:")
    try:
        rag_result = await rag_client.calculate_score(
            certificate_text=test_text,
            student_info={"student_id": "TEST_MATH"}
        )
        print(f"  类别: {rag_result.get('category')}")
        print(f"  分数: {rag_result.get('score')}")
        print(f"  置信度: {rag_result.get('confidence')}")
        print(f"  使用RAG: {rag_result.get('rag_used')}")
        print(f"  理由: {rag_result.get('reason', 'N/A')}")
    except Exception as e:
        print(f"  RAG调用失败: {e}")

    print("\n[2] 完整分类流程:")
    result = await cert_service.classify_and_calculate_score(
        certificate_text=test_text,
        certificate_info={"title": "数学建模竞赛一等奖"},
        student_info={"student_id": "TEST_MATH2"}
    )
    print(f"  最终类别: {result.get('category')}")
    print(f"  最终分数: {result.get('score')}")
    print(f"  方法: {result.get('method')}")
    print(f"  理由: {result.get('reason')}")

    print("\n" + "=" * 70)
    print("预期结果: A类, 20分 (省部级一等奖)")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_math_modeling())
