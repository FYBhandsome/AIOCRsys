#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG服务关键API端点测试脚本
测试用户指定的4个关键API端点
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List


class KeyAPITester:
    """关键API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
        self.session = requests.Session()
        self.test_results: List[Dict[str, Any]] = []
    
    def log_test(self, test_name: str, endpoint: str, method: str, 
                 status_code: int, success: bool, response_time: float, 
                 message: str = "", data: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "success": success,
            "response_time_ms": round(response_time, 2),
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}")
        print(f"   端点: {method} {endpoint}")
        print(f"   状态码: {status_code}")
        print(f"   响应时间: {response_time:.2f}ms")
        if message:
            print(f"   说明: {message}")
        print()
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> tuple:
        """发送HTTP请求并返回结果"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, **kwargs)
            elif method.upper() == "POST":
                response = self.session.post(url, **kwargs)
            else:
                return None, 0, f"不支持的HTTP方法: {method}"
            
            response_time = (time.time() - start_time) * 1000
            return response, response_time, None
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return None, response_time, "无法连接到服务器"
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return None, response_time, "请求超时"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return None, response_time, str(e)
    
    def test_1_system_health(self):
        """测试1: GET /api/v1/system/health"""
        test_name = "系统健康检查"
        endpoint = f"{self.api_prefix}/system/health"
        method = "GET"
        
        response, response_time, error = self.make_request(method, endpoint)
        
        if error:
            self.log_test(test_name, endpoint, method, 0, False, 
                        response_time, error)
            return
        
        status_code = response.status_code
        success = status_code == 200
        
        try:
            data = response.json()
        except:
            data = None
        
        message = f"返回200 OK" if success else f"状态码: {status_code}"
        self.log_test(test_name, endpoint, method, status_code, success, 
                    response_time, message, data)
    
    def test_2_chat(self):
        """测试2: POST /api/v1/chat"""
        test_name = "聊天API"
        endpoint = f"{self.api_prefix}/chat"
        method = "POST"
        
        payload = {
            "message": "你好，请介绍一下综测加分规则",
            "chat_history": []
        }
        
        response, response_time, error = self.make_request(
            method, endpoint, json=payload, timeout=60
        )
        
        if error:
            self.log_test(test_name, endpoint, method, 0, False, 
                        response_time, error)
            return
        
        status_code = response.status_code
        success = status_code == 200
        
        try:
            data = response.json()
        except:
            data = None
        
        message = f"返回200 OK" if success else f"状态码: {status_code}"
        self.log_test(test_name, endpoint, method, status_code, success, 
                    response_time, message, data)
    
    def test_3_certificate_calculate(self):
        """测试3: POST /api/v1/certificate/calculate"""
        test_name = "证书加分计算"
        endpoint = f"{self.api_prefix}/certificate/calculate"
        method = "POST"
        
        payload = {
            "certificate_text": "获得全国大学生数学建模竞赛省级一等奖",
            "student_info": {"grade": "2023"}
        }
        
        response, response_time, error = self.make_request(
            method, endpoint, json=payload, timeout=60
        )
        
        if error:
            self.log_test(test_name, endpoint, method, 0, False, 
                        response_time, error)
            return
        
        status_code = response.status_code
        success = status_code == 200
        
        try:
            data = response.json()
        except:
            data = None
        
        message = f"返回200 OK" if success else f"状态码: {status_code}"
        self.log_test(test_name, endpoint, method, status_code, success, 
                    response_time, message, data)
    
    def test_4_documents(self):
        """测试4: GET /api/v1/documents"""
        test_name = "文档列表"
        endpoint = f"{self.api_prefix}/documents"
        method = "GET"
        
        response, response_time, error = self.make_request(method, endpoint)
        
        if error:
            self.log_test(test_name, endpoint, method, 0, False, 
                        response_time, error)
            return
        
        status_code = response.status_code
        success = status_code in [200, 404]
        
        try:
            data = response.json()
        except:
            data = None
        
        message = f"返回{status_code} (符合预期)" if success else f"状态码: {status_code}"
        self.log_test(test_name, endpoint, method, status_code, success, 
                    response_time, message, data)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("RAG服务关键API端点测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"服务地址: {self.base_url}")
        print("=" * 80)
        print()
        
        print("--- 开始测试 ---")
        print()
        
        self.test_1_system_health()
        self.test_2_chat()
        self.test_3_certificate_calculate()
        self.test_4_documents()
        
        print("=" * 80)
        print("测试摘要:")
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"  总测试数: {total}")
        print(f"  ✅ 通过: {passed}")
        print(f"  ❌ 失败: {failed}")
        print()
        
        print("详细响应时间:")
        for result in self.test_results:
            print(f"  {result['test_name']}: {result['response_time_ms']}ms")
        
        print("=" * 80)
        
        return self.test_results
    
    def save_results(self, filename: str = "key_api_test_results.json"):
        """保存测试结果到文件"""
        results_file = project_root / "tests" / filename
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "test_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        print(f"\n测试结果已保存到: {results_file}")


if __name__ == "__main__":
    tester = KeyAPITester(base_url="http://localhost:8010")
    results = tester.run_all_tests()
    tester.save_results()
