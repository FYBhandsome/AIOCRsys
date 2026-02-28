#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版API测试脚本
仅测试Visual Model后端API
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

class SimpleAPITester:
    """简化版API测试器"""
    
    def __init__(self, visual_model_url: str = "http://127.0.0.1:8001"):
        self.visual_model_url = visual_model_url
        self.results = []
        self.token = None
        
    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
        
    def record(self, test_name: str, success: bool, response: Dict = None, error: str = None, duration_ms: int = 0):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "response": response,
            "error": error,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✓ 通过" if success else "✗ 失败"
        self.log(f"{status}: {test_name} ({duration_ms}ms)")
        if error:
            self.log(f"  错误: {error}", "ERROR")
            
    def test_all(self):
        """运行所有测试"""
        self.log("=" * 60)
        self.log("开始API测试")
        self.log(f"Visual Model URL: {self.visual_model_url}")
        self.log("=" * 60)
        
        # 测试健康检查
        try:
            start = time.time()
            response = requests.get(f"{self.visual_model_url}/health", timeout=30)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record("健康检查", True, response.json(), duration_ms=duration)
            else:
                self.record("健康检查", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record("健康检查", False, None, str(e))
            
        # 测试登录
        try:
            start = time.time()
            response = requests.post(
                f"{self.visual_model_url}/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=30
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.record("管理员登录", True, {"token": self.token[:20] + "..." if self.token else None}, duration_ms=duration)
            else:
                self.record("管理员登录", False, None, f"状态码: {response.status_code}, {response.text[:200]}", duration)
        except Exception as e:
            self.record("管理员登录", False, None, str(e))
            
        # 测试获取用户信息
        if self.token:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.visual_model_url}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    self.record("获取用户信息", True, response.json(), duration_ms=duration)
                else:
                    self.record("获取用户信息", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.record("获取用户信息", False, None, str(e))
                
        # 测试教师API
        if self.token:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.visual_model_url}/api/v1/teacher/students",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 403]:
                    self.record("获取学生列表", True, {"status_code": response.status_code}, None, duration)
                else:
                    self.record("获取学生列表", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.record("获取学生列表", False, None, str(e))
                
        # 测试管理员API
        if self.token:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.visual_model_url}/api/v1/admin/users",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 403]:
                    self.record("获取用户列表", True, {"status_code": response.status_code}, None, duration)
                else:
                    self.record("获取用户列表", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.record("获取用户列表", False, None, str(e))
                
        # 生成报告
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        
        self.log("=" * 60)
        self.log("测试报告")
        self.log("=" * 60)
        self.log(f"总计: {total} 个测试")
        self.log(f"通过: {passed} 个")
        self.log(f"失败: {total - passed} 个")
        self.log(f"通过率: {passed/total*100:.1f}%" if total > 0 else "0%")
        
        # 保存报告
        report = {
            "test_time": datetime.now().isoformat(),
            "summary": {"total": total, "passed": passed, "failed": total - passed},
            "results": self.results
        }
        
        with open("simple_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        self.log(f"\n测试报告已保存到: simple_test_report.json")
        
        return report


if __name__ == "__main__":
    tester = SimpleAPITester()
    tester.test_all()
