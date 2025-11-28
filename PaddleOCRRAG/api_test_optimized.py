#!/usr/bin/env python3
"""
优化后的API测试脚本
测试所有API端点的功能
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

class OptimizedAPITester:
    """优化后的API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化测试器
        
        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if not success and data:
            print(f"   详细信息: {data}")
        print()
    
    def test_health_check(self):
        """测试健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/system/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("健康检查", True, "系统健康状态正常")
                else:
                    self.log_test("健康检查", False, "系统健康状态异常", data)
            else:
                self.log_test("健康检查", False, f"HTTP状态码: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("健康检查", False, f"请求失败: {str(e)}")
    
    def test_system_info(self):
        """测试系统信息"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/system/info")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("系统信息", True, "获取系统信息成功")
                else:
                    self.log_test("系统信息", False, "获取系统信息失败", data)
            else:
                self.log_test("系统信息", False, f"HTTP状态码: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("系统信息", False, f"请求失败: {str(e)}")
    
    def test_certificate_calculation(self):
        """测试证书加分计算"""
        try:
            test_data = {
                "certificate_text": "张三获得2023年全国大学生数学建模竞赛一等奖",
                "student_info": {
                    "年级": "大三",
                    "专业": "计算机科学与技术"
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/certificate/calculate",
                json=test_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_data = data.get("data", {})
                    score = result_data.get("score", 0)
                    category = result_data.get("category", "未知")
                    self.log_test("证书加分计算", True, f"计算成功 - 类别: {category}, 分数: {score}")
                else:
                    self.log_test("证书加分计算", False, "计算失败", data)
            else:
                self.log_test("证书加分计算", False, f"HTTP状态码: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("证书加分计算", False, f"请求失败: {str(e)}")
    
    def test_chat(self):
        """测试AI对话"""
        try:
            test_data = {
                "message": "你好，我想了解英语四级证书的加分规则",
                "use_rag": True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/chat",
                json=test_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_data = data.get("data", {})
                    answer = result_data.get("answer", "")
                    self.log_test("AI对话", True, f"对话成功 - 回复长度: {len(answer)}字符")
                else:
                    self.log_test("AI对话", False, "对话失败", data)
            else:
                self.log_test("AI对话", False, f"HTTP状态码: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("AI对话", False, f"请求失败: {str(e)}")
    
    def test_document_list(self):
        """测试文档列表"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/documents")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_data = data.get("data", {})
                    total = result_data.get("total", 0)
                    self.log_test("文档列表", True, f"获取成功 - 文档总数: {total}")
                else:
                    self.log_test("文档列表", False, "获取失败", data)
            else:
                self.log_test("文档列表", False, f"HTTP状态码: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("文档列表", False, f"请求失败: {str(e)}")
    
    def test_prompts(self):
        """测试Prompt管理"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/prompts")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_data = data.get("data", {})
                    prompts_count = len(result_data.get("prompts", []))
                    self.log_test("Prompt管理", True, f"获取成功 - Prompt数量: {prompts_count}")
                else:
                    self.log_test("Prompt管理", False, "获取失败", data)
            else:
                self.log_test("Prompt管理", False, f"HTTP状态码: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Prompt管理", False, f"请求失败: {str(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🚀 开始运行优化后的API测试")
        print("=" * 60)
        print()
        
        # 基础系统测试
        print("📋 基础系统测试")
        print("-" * 30)
        self.test_health_check()
        self.test_system_info()
        
        # 核心功能测试
        print("🎯 核心功能测试")
        print("-" * 30)
        self.test_certificate_calculation()
        self.test_chat()
        
        # 管理功能测试
        print("⚙️ 管理功能测试")
        print("-" * 30)
        self.test_document_list()
        self.test_prompts()
        
        # 测试结果统计
        self.print_summary()
    
    def print_summary(self):
        """打印测试结果摘要"""
        print("=" * 60)
        print("📊 测试结果摘要")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"通过率: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        if failed_tests > 0:
            print("失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print()
        print("测试完成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def save_results(self, filename: str = "test_results_optimized.json"):
        """保存测试结果到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_summary": {
                        "total_tests": len(self.test_results),
                        "passed_tests": sum(1 for r in self.test_results if r["success"]),
                        "failed_tests": sum(1 for r in self.test_results if not r["success"]),
                        "test_time": datetime.now().isoformat()
                    },
                    "test_results": self.test_results
                }, f, ensure_ascii=False, indent=2)
            print(f"测试结果已保存到: {filename}")
        except Exception as e:
            print(f"保存测试结果失败: {str(e)}")


def main():
    """主函数"""
    print("🔧 优化后的PaddleOCRRAG API测试工具")
    print()
    
    # 检查服务是否运行
    tester = OptimizedAPITester()
    
    try:
        response = requests.get(f"{tester.base_url}/", timeout=5)
        print(f"✅ 服务运行正常 - {tester.base_url}")
        print()
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务: {tester.base_url}")
        print(f"错误: {str(e)}")
        print()
        print("请确保服务已启动:")
        print("  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return
    
    # 运行测试
    tester.run_all_tests()
    
    # 保存结果
    tester.save_results()


if __name__ == "__main__":
    main()
