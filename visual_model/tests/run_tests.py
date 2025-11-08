#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一测试套件 - 综合认证、API和新功能测试

运行方式：
    python visual_model/tests/run_tests.py [test_type]
    
    test_type: 
        - auth: 仅认证系统测试
        - api: 仅API测试
        - all: 所有测试 (默认)
"""

import sys
import os
import asyncio
import requests
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 修复Windows控制台编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# API配置
BASE_URL = "http://localhost:8001/api/v1"
TIMEOUT = 10


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


class UnifiedTester:
    """统一测试器"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.stats = {
            'passed': 0,
            'failed': 0,
            'total': 0
        }
    
    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}{Colors.END}")
    
    def print_success(self, text: str):
        """打印成功信息"""
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")
    
    def print_error(self, text: str):
        """打印错误信息"""
        print(f"{Colors.RED}✗ {text}{Colors.END}")
    
    def print_info(self, text: str):
        """打印信息"""
        print(f"{Colors.BLUE}ℹ {text}{Colors.END}")
    
    def test(self, name: str, func):
        """执行测试"""
        self.stats['total'] += 1
        print(f"\n{Colors.BOLD}测试 {self.stats['total']}: {name}{Colors.END}")
        try:
            func()
            self.stats['passed'] += 1
            self.print_success(f"{name} - 通过")
            return True
        except AssertionError as e:
            self.stats['failed'] += 1
            self.print_error(f"{name} - 失败: {str(e)}")
            return False
        except Exception as e:
            self.stats['failed'] += 1
            self.print_error(f"{name} - 错误: {str(e)}")
            return False
    
    def check_server(self):
        """检查服务器状态"""
        try:
            response = requests.get(f"{self.base_url.replace('/api/v1', '')}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def register_user(self, username: str, password: str, email: str, 
                     role: str = "student", student_id: str = None):
        """注册用户"""
        url = f"{self.base_url}/auth/register"
        data = {
            "username": username,
            "password": password,
            "email": email,
            "role": role,
            "real_name": f"测试用户_{role}"
        }
        if student_id:
            data["student_id"] = student_id
        
        response = requests.post(url, json=data, timeout=TIMEOUT)
        
        if response.status_code == 200:
            self.print_success(f"用户 {username} 注册成功")
            return response.json()
        elif "已存在" in response.text:
            self.print_info(f"用户 {username} 已存在")
            return {"message": "用户已存在"}
        else:
            raise Exception(f"注册失败: {response.status_code} - {response.text}")
    
    def login_user(self, username: str, password: str):
        """用户登录"""
        url = f"{self.base_url}/auth/login"
        data = {"username": username, "password": password}
        
        response = requests.post(url, json=data, timeout=TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            self.token = result['access_token']
            self.print_success(f"用户 {username} 登录成功")
            return result
        else:
            raise Exception(f"登录失败: {response.status_code} - {response.text}")
    
    def run_auth_tests(self):
        """运行认证系统测试"""
        self.print_header("认证系统测试")
        
        # 检查服务器
        self.print_info("检查服务器连接...")
        if not self.check_server():
            self.print_error("无法连接到后端服务器 (http://localhost:8001)")
            return False
        self.print_success("服务器连接正常")
        
        # 测试1: 注册验证
        def test_register_validation():
            url = f"{self.base_url}/auth/register"
            response = requests.post(url, json={
                "username": "",
                "password": "password123",
                "email": "test@test.com",
                "role": "student"
            }, timeout=TIMEOUT)
            assert response.status_code == 422, "应该拒绝空用户名"
            self.print_info("✓ 空用户名验证通过")
        
        self.test("注册表单验证", test_register_validation)
        
        # 测试2-4: 注册不同角色用户
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        self.test("注册学生用户", lambda: self.register_user(
            f"test_student_{timestamp}", "password123", 
            f"student_{timestamp}@test.com", "student", f"2024{timestamp}"
        ))
        
        self.test("注册教师用户", lambda: self.register_user(
            f"test_teacher_{timestamp}", "password123",
            f"teacher_{timestamp}@test.com", "teacher"
        ))
        
        self.test("注册管理员用户", lambda: self.register_user(
            f"test_admin_{timestamp}", "password123",
            f"admin_{timestamp}@test.com", "admin"
        ))
        
        # 测试5: 登录测试
        def test_login():
            result = self.login_user(f"test_student_{timestamp}", "password123")
            assert 'access_token' in result
        
        self.test("学生用户登录", test_login)
        
        return True
    
    async def run_api_tests(self):
        """运行API测试"""
        self.print_header("API功能测试")
        
        # 简化的API测试
        async def test_api_endpoint(name: str, method: str, endpoint: str):
            url = f"{self.base_url.replace('/api/v1', '')}{endpoint}"
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    if method == "GET":
                        response = await client.get(url, headers=headers)
                    elif method == "POST":
                        response = await client.post(url, headers=headers)
                    
                    if response.status_code < 400:
                        self.print_success(f"{name} - {response.status_code}")
                        self.stats['passed'] += 1
                    else:
                        self.print_error(f"{name} - {response.status_code}")
                        self.stats['failed'] += 1
            except Exception as e:
                self.print_error(f"{name} - 错误: {e}")
                self.stats['failed'] += 1
        
        # 测试健康检查
        await test_api_endpoint("健康检查", "GET", "/health")
        await test_api_endpoint("API信息", "GET", "/api/v1/auth/me")
        
        return True
    
    def print_summary(self):
        """打印测试统计"""
        self.print_header("测试结果汇总")
        print(f"总测试数: {Colors.BOLD}{self.stats['total']}{Colors.END}")
        print(f"通过: {Colors.GREEN}{self.stats['passed']}{Colors.END}")
        print(f"失败: {Colors.RED}{self.stats['failed']}{Colors.END}")
        
        success_rate = (self.stats['passed'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        
        if self.stats['failed'] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 所有测试通过！{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ 有 {self.stats['failed']} 个测试失败{Colors.END}")
        
        return self.stats['failed'] == 0


def main():
    """主函数"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║           综合测试套件                                     ║")
    print("║           Unified Test Suite                              ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(Colors.END)
    
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    tester = UnifiedTester()
    
    try:
        if test_type in ['auth', 'all']:
            tester.run_auth_tests()
        
        if test_type in ['api', 'all']:
            asyncio.run(tester.run_api_tests())
        
        success = tester.print_summary()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}测试运行出错: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

