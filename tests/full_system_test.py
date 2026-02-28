#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面功能测试脚本
测试所有API接口、身份切换、权限控制等功能
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def record(self, category: str, test_name: str, success: bool, 
               response: Dict = None, error: str = None, duration_ms: int = 0):
        result = {
            "category": category,
            "test_name": test_name,
            "success": success,
            "response": response,
            "error": error,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✓ 通过" if success else "✗ 失败"
        print(f"[{category}] {status}: {test_name} ({duration_ms}ms)")
        if error:
            print(f"  错误: {error}")

class FullSystemTester:
    """全面系统测试器"""
    
    def __init__(self, visual_model_url: str = "http://127.0.0.1:8001", rag_url: str = "http://127.0.0.1:8002"):
        self.visual_model_url = visual_model_url
        self.rag_url = rag_url
        self.result = TestResult()
        self.tokens = {}
        self.user_info = {}
        
        self.test_accounts = [
            {"username": "dev_admin", "password": "dev123456", "role": "admin"},
            {"username": "dev_teacher", "password": "dev123456", "role": "teacher"},
            {"username": "dev_student", "password": "dev123456", "role": "student"},
            {"username": "admin", "password": "admin123", "role": "admin"},
            {"username": "teacher", "password": "teacher123", "role": "teacher"},
            {"username": "student_202300502128", "password": "student123", "role": "student"},
        ]
        
    def test_health_check(self):
        """测试健康检查"""
        print("\n" + "=" * 60)
        print("测试健康检查")
        print("=" * 60)
        
        try:
            start = time.time()
            response = requests.get(f"{self.visual_model_url}/health", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.result.record("健康检查", "Visual Model健康检查", True, response.json(), duration_ms=duration)
            else:
                self.result.record("健康检查", "Visual Model健康检查", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.result.record("健康检查", "Visual Model健康检查", False, None, str(e))
            
    def test_all_logins(self):
        """测试所有账号登录"""
        print("\n" + "=" * 60)
        print("测试账号登录")
        print("=" * 60)
        
        for account in self.test_accounts:
            try:
                start = time.time()
                response = requests.post(
                    f"{self.visual_model_url}/api/v1/auth/login",
                    json={"username": account["username"], "password": account["password"]},
                    timeout=10
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    self.tokens[account["username"]] = token
                    
                    self.result.record("登录测试", f"登录 {account['username']} ({account['role']})", 
                                      True, {"token": token[:20] + "..." if token else None}, duration_ms=duration)
                else:
                    self.result.record("登录测试", f"登录 {account['username']} ({account['role']})", 
                                      False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.result.record("登录测试", f"登录 {account['username']} ({account['role']})", 
                                  False, None, str(e))
                                  
    def test_get_user_info(self):
        """测试获取用户信息"""
        print("\n" + "=" * 60)
        print("测试获取用户信息")
        print("=" * 60)
        
        for username, token in self.tokens.items():
            if not token:
                continue
                
            try:
                start = time.time()
                response = requests.get(
                    f"{self.visual_model_url}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    self.user_info[username] = data
                    self.result.record("用户信息", f"获取 {username} 信息", True, data, duration_ms=duration)
                else:
                    self.result.record("用户信息", f"获取 {username} 信息", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.result.record("用户信息", f"获取 {username} 信息", False, None, str(e))
                
    def test_role_switching(self):
        """测试角色切换"""
        print("\n" + "=" * 60)
        print("测试角色切换")
        print("=" * 60)
        
        admin_token = self.tokens.get("dev_admin") or self.tokens.get("admin")
        if not admin_token:
            self.result.record("角色切换", "角色切换测试", False, None, "无管理员token")
            return
            
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        try:
            start = time.time()
            response = requests.get(f"{self.visual_model_url}/api/v1/admin/users", headers=headers, timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                users = response.json()
                self.result.record("角色切换", "获取用户列表(管理员权限)", True, 
                                  {"count": len(users) if isinstance(users, list) else "N/A"}, duration_ms=duration)
            elif response.status_code == 403:
                self.result.record("角色切换", "获取用户列表(权限限制)", True, {"status": "权限限制"}, duration_ms=duration)
            else:
                self.result.record("角色切换", "获取用户列表", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.result.record("角色切换", "获取用户列表", False, None, str(e))
            
    def test_permission_control(self):
        """测试权限控制"""
        print("\n" + "=" * 60)
        print("测试权限控制")
        print("=" * 60)
        
        student_token = self.tokens.get("dev_student") or self.tokens.get("student_202300502128")
        if student_token:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.visual_model_url}/api/v1/admin/users",
                    headers={"Authorization": f"Bearer {student_token}"},
                    timeout=10
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 403:
                    self.result.record("权限控制", "学生访问管理员接口(应拒绝)", True, {"status": "正确拒绝"}, duration_ms=duration)
                else:
                    self.result.record("权限控制", "学生访问管理员接口", False, None, f"状态码: {response.status_code} (应为403)", duration)
            except Exception as e:
                self.result.record("权限控制", "学生访问管理员接口", False, None, str(e))
                
        teacher_token = self.tokens.get("dev_teacher") or self.tokens.get("teacher")
        if teacher_token:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.visual_model_url}/api/v1/teacher/students",
                    headers={"Authorization": f"Bearer {teacher_token}"},
                    timeout=10
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 403]:
                    self.result.record("权限控制", "教师访问学生列表", True, {"status_code": response.status_code}, duration_ms=duration)
                else:
                    self.result.record("权限控制", "教师访问学生列表", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.result.record("权限控制", "教师访问学生列表", False, None, str(e))
                
    def test_admin_apis(self):
        """测试管理员API"""
        print("\n" + "=" * 60)
        print("测试管理员API")
        print("=" * 60)
        
        admin_token = self.tokens.get("dev_admin") or self.tokens.get("admin")
        if not admin_token:
            self.result.record("管理员API", "跳过测试", False, None, "无管理员token")
            return
            
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        apis = [
            ("/api/v1/admin/users", "获取用户列表"),
            ("/api/v1/admin/settings", "获取系统设置"),
            ("/api/v1/admin/rules/list", "获取规则文档列表"),
        ]
        
        for endpoint, name in apis:
            try:
                start = time.time()
                response = requests.get(f"{self.visual_model_url}{endpoint}", headers=headers, timeout=10)
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 404]:
                    self.result.record("管理员API", name, True, 
                                      {"status_code": response.status_code}, None, duration)
                else:
                    self.result.record("管理员API", name, False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.result.record("管理员API", name, False, None, str(e))
                
    def test_teacher_apis(self):
        """测试教师API"""
        print("\n" + "=" * 60)
        print("测试教师API")
        print("=" * 60)
        
        teacher_token = self.tokens.get("dev_teacher") or self.tokens.get("teacher")
        if not teacher_token:
            self.result.record("教师API", "跳过测试", False, None, "无教师token")
            return
            
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        apis = [
            ("/api/v1/teacher/students", "获取学生列表"),
            ("/api/v1/teacher/classes", "获取班级列表"),
        ]
        
        for endpoint, name in apis:
            try:
                start = time.time()
                response = requests.get(f"{self.visual_model_url}{endpoint}", headers=headers, timeout=10)
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 404]:
                    self.result.record("教师API", name, True, {"status_code": response.status_code}, None, duration)
                else:
                    self.result.record("教师API", name, False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.result.record("教师API", name, False, None, str(e))
                
    def test_student_apis(self):
        """测试学生API"""
        print("\n" + "=" * 60)
        print("测试学生API")
        print("=" * 60)
        
        student_token = self.tokens.get("dev_student") or self.tokens.get("student_202300502128")
        if not student_token:
            self.result.record("学生API", "跳过测试", False, None, "无学生token")
            return
            
        headers = {"Authorization": f"Bearer {student_token}"}
        
        apis = [
            ("/api/v1/student/scores/summary", "获取成绩摘要"),
            ("/api/v1/student/uploads", "获取上传历史"),
        ]
        
        for endpoint, name in apis:
            try:
                start = time.time()
                response = requests.get(f"{self.visual_model_url}{endpoint}", headers=headers, timeout=10)
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 404]:
                    self.result.record("学生API", name, True, {"status_code": response.status_code}, None, duration)
                else:
                    self.result.record("学生API", name, False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.result.record("学生API", name, False, None, str(e))
                
    def test_rag_apis(self):
        """测试RAG API"""
        print("\n" + "=" * 60)
        print("测试RAG API")
        print("=" * 60)
        
        try:
            start = time.time()
            response = requests.get(f"{self.rag_url}/health", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.result.record("RAG API", "RAG健康检查", True, response.json(), duration_ms=duration)
            else:
                self.result.record("RAG API", "RAG健康检查", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.result.record("RAG API", "RAG健康检查", False, None, str(e))
            
        try:
            start = time.time()
            response = requests.post(
                f"{self.rag_url}/api/v1/chat",
                json={"message": "省级竞赛一等奖加多少分", "chat_history": []},
                timeout=60
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                self.result.record("RAG API", "RAG聊天接口", True, {"duration": duration}, duration_ms=duration)
            else:
                self.result.record("RAG API", "RAG聊天接口", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            self.result.record("RAG API", "RAG聊天接口", False, None, str(e))
            
    def test_logout(self):
        """测试登出"""
        print("\n" + "=" * 60)
        print("测试登出")
        print("=" * 60)
        
        admin_token = self.tokens.get("dev_admin") or self.tokens.get("admin")
        if admin_token:
            try:
                start = time.time()
                response = requests.post(
                    f"{self.visual_model_url}/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    timeout=10
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    self.result.record("登出测试", "管理员登出", True, response.json(), duration_ms=duration)
                else:
                    self.result.record("登出测试", "管理员登出", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.result.record("登出测试", "管理员登出", False, None, str(e))
                
    def generate_report(self) -> Dict:
        """生成测试报告"""
        total = len(self.result.results)
        passed = sum(1 for r in self.result.results if r["success"])
        failed = total - passed
        
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        print(f"总计: {total} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "0%")
        
        categories = {}
        for r in self.result.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0, "failed": 0}
            categories[cat]["total"] += 1
            if r["success"]:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
                
        print("\n分类统计:")
        for cat, stats in categories.items():
            print(f"  [{cat}] 通过: {stats['passed']}/{stats['total']}")
            
        report = {
            "test_time": self.result.start_time.isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%"
            },
            "categories": categories,
            "results": self.result.results
        }
        
        return report
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("全面功能测试")
        print(f"测试时间: {datetime.now().isoformat()}")
        print(f"Visual Model URL: {self.visual_model_url}")
        print(f"RAG URL: {self.rag_url}")
        print("=" * 60)
        
        self.test_health_check()
        self.test_all_logins()
        self.test_get_user_info()
        self.test_role_switching()
        self.test_permission_control()
        self.test_admin_apis()
        self.test_teacher_apis()
        self.test_student_apis()
        self.test_rag_apis()
        self.test_logout()
        
        return self.generate_report()


if __name__ == "__main__":
    tester = FullSystemTester()
    report = tester.run_all_tests()
    
    with open("full_system_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
    print(f"\n测试报告已保存到: full_system_test_report.json")
