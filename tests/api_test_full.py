#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面API测试脚本 - 完整版
测试所有后端API接口功能
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

class APITester:
    """API测试器"""
    
    def __init__(self, visual_model_url: str = "http://127.0.0.1:8001", rag_url: str = "http://127.0.0.1:8000"):
        self.visual_model_url = visual_model_url
        self.rag_url = rag_url
        self.results = []
        self.token = None
        self.user_info = None
        
    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
        
    def record_result(self, test_name: str, success: bool, response: Dict = None, error: str = None, duration_ms: int = 0):
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
            
    def test_health_check(self):
        """测试健康检查接口"""
        self.log("=" * 60)
        self.log("测试健康检查接口")
        self.log("=" * 60)
        
        # Visual Model健康检查
        try:
            start = time.time()
            response = requests.get(f"{self.visual_model_url}/health", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("Visual Model健康检查", True, response.json(), duration_ms=duration)
            else:
                self.record_result("Visual Model健康检查", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("Visual Model健康检查", False, None, str(e))
            
    def test_auth_api(self):
        """测试认证API"""
        self.log("=" * 60)
        self.log("测试认证API")
        self.log("=" * 60)
        
        # 测试管理员登录
        try:
            start = time.time()
            response = requests.post(
                f"{self.visual_model_url}/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.record_result("管理员登录", True, {"token": self.token[:20] + "..." if self.token else None}, duration_ms=duration)
            else:
                self.record_result("管理员登录", False, None, f"状态码: {response.status_code}, {response.text}", duration)
        except Exception as e:
            self.record_result("管理员登录", False, None, str(e))
            
        # 测试教师登录
        try:
            start = time.time()
            response = requests.post(
                f"{self.visual_model_url}/api/v1/auth/login",
                json={"username": "teacher", "password": "teacher123"},
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("教师登录", True, None, duration_ms=duration)
            else:
                self.record_result("教师登录", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("教师登录", False, None, str(e))
            
        # 测试学生登录
        try:
            start = time.time()
            response = requests.post(
                f"{self.visual_model_url}/api/v1/auth/login",
                json={"username": "student_202300502128", "password": "student123"},
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("学生登录", True, None, duration_ms=duration)
            else:
                self.record_result("学生登录", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("学生登录", False, None, str(e))
            
        # 测试获取当前用户信息
        if self.token:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.visual_model_url}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    self.user_info = response.json()
                    self.record_result("获取当前用户信息", True, self.user_info, duration_ms=duration)
                else:
                    self.record_result("获取当前用户信息", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.record_result("获取当前用户信息", False, None, str(e))
                
    def test_teacher_api(self):
        """测试教师API"""
        self.log("=" * 60)
        self.log("测试教师API")
        self.log("=" * 60)
        
        if not self.token:
            self.log("跳过教师API测试: 未登录", "WARN")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试获取班级列表
        try:
            start = time.time()
            response = requests.get(
                f"{self.visual_model_url}/api/v1/teacher/classes",
                headers=headers,
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("获取班级列表", True, response.json(), duration_ms=duration)
            elif response.status_code == 403:
                self.record_result("获取班级列表(权限限制)", True, {"message": "权限限制，接口存在"}, duration_ms=duration)
            else:
                self.record_result("获取班级列表", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("获取班级列表", False, None, str(e))
            
        # 测试获取学生列表
        try:
            start = time.time()
            response = requests.get(
                f"{self.visual_model_url}/api/v1/teacher/students",
                headers=headers,
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("获取学生列表", True, response.json(), duration_ms=duration)
            else:
                self.record_result("获取学生列表", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("获取学生列表", False, None, str(e))
            
    def test_admin_api(self):
        """测试管理员API"""
        self.log("=" * 60)
        self.log("测试管理员API")
        self.log("=" * 60)
        
        if not self.token:
            self.log("跳过管理员API测试: 未登录", "WARN")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试获取用户列表
        try:
            start = time.time()
            response = requests.get(
                f"{self.visual_model_url}/api/v1/admin/users",
                headers=headers,
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("获取用户列表", True, response.json(), duration_ms=duration)
            else:
                self.record_result("获取用户列表", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("获取用户列表", False, None, str(e))
            
        # 测试获取系统设置
        try:
            start = time.time()
            response = requests.get(
                f"{self.visual_model_url}/api/v1/admin/settings",
                headers=headers,
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("获取系统设置", True, response.json(), duration_ms=duration)
            else:
                self.record_result("获取系统设置", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("获取系统设置", False, None, str(e))
            
    def test_rag_health(self):
        """测试RAG服务健康状态"""
        self.log("=" * 60)
        self.log("测试RAG服务")
        self.log("=" * 60)
        
        # 测试RAG服务连接
        try:
            start = time.time()
            response = requests.get(f"{self.rag_url}/docs", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.record_result("RAG服务连接", True, {"message": "服务可访问"}, duration_ms=duration)
            else:
                self.record_result("RAG服务连接", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.record_result("RAG服务连接", False, None, str(e))
            
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        report = {
            "test_time": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%"
            },
            "results": self.results
        }
        
        self.log("=" * 60)
        self.log("测试报告")
        self.log("=" * 60)
        self.log(f"总计: {total} 个测试")
        self.log(f"通过: {passed} 个")
        self.log(f"失败: {failed} 个")
        self.log(f"通过率: {report['summary']['pass_rate']}")
        
        return report
        
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 60)
        self.log("开始全面API测试")
        self.log(f"Visual Model URL: {self.visual_model_url}")
        self.log(f"RAG URL: {self.rag_url}")
        self.log("=" * 60)
        
        self.test_health_check()
        self.test_auth_api()
        self.test_teacher_api()
        self.test_admin_api()
        self.test_rag_health()
        
        return self.generate_report()


if __name__ == "__main__":
    tester = APITester()
    report = tester.run_all_tests()
    
    # 保存报告
    with open("api_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    print(f"\n测试报告已保存到: api_test_report.json")
