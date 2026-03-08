#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统统一API测试脚本
测试所有API端点的功能

使用方法:
    python tests/test_api.py                    # 运行所有测试
    python tests/test_api.py --quick            # 快速测试（仅核心功能）
    python tests/test_api.py --save             # 保存测试结果
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
from typing import Dict, Any, List, Optional


class RAGAPITester:
    """RAG系统API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
        self.session = requests.Session()
        self.test_results: List[Dict[str, Any]] = []
        self.passed_count = 0
        self.failed_count = 0
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None, response_time: float = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "response_time_ms": response_time
        }
        self.test_results.append(result)
        
        if success:
            self.passed_count += 1
            status = "✅ 通过"
        else:
            self.failed_count += 1
            status = "❌ 失败"
        
        time_info = f" ({response_time:.0f}ms)" if response_time else ""
        print(f"{status}: {test_name}{time_info}")
        if message:
            print(f"   {message}")
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
            elif method.upper() == "PUT":
                response = self.session.put(url, **kwargs)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, **kwargs)
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
    
    def test_root_endpoint(self) -> bool:
        """测试根路径"""
        response, response_time, error = self.make_request("GET", "/")
        
        if error:
            self.log_test("根路径", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("根路径", True, f"服务状态: {data.get('status', 'unknown')}", data=data, response_time=response_time)
            return True
        else:
            self.log_test("根路径", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_health_check(self) -> bool:
        """测试健康检查"""
        response, response_time, error = self.make_request("GET", "/health")
        
        if error:
            self.log_test("健康检查", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("健康检查", True, f"状态: {data.get('status', 'unknown')}", data=data, response_time=response_time)
            return True
        else:
            self.log_test("健康检查", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_system_info(self) -> bool:
        """测试系统信息"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/system/info")
        
        if error:
            self.log_test("系统信息", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("系统信息", True, f"服务版本: {data.get('data', {}).get('version', 'unknown')}", response_time=response_time)
            return True
        else:
            self.log_test("系统信息", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_system_health(self) -> bool:
        """测试系统健康检查"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/system/health")
        
        if error:
            self.log_test("系统健康检查", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            healthy = data.get("data", {}).get("healthy", False)
            self.log_test("系统健康检查", True, f"健康状态: {healthy}", response_time=response_time)
            return True
        else:
            self.log_test("系统健康检查", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_system_config(self) -> bool:
        """测试获取系统配置"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/system/config")
        
        if error:
            self.log_test("获取系统配置", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("获取系统配置", True, "配置获取成功", response_time=response_time)
            return True
        else:
            self.log_test("获取系统配置", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_llm_config(self) -> bool:
        """测试获取LLM配置"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/system/llm/config")
        
        if error:
            self.log_test("获取LLM配置", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("获取LLM配置", True, "LLM配置获取成功", response_time=response_time)
            return True
        else:
            self.log_test("获取LLM配置", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_vector_db_stats(self) -> bool:
        """测试向量数据库统计"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/vector-db/stats")
        
        if error:
            self.log_test("向量数据库统计", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            doc_count = data.get("total_documents", 0)
            self.log_test("向量数据库统计", True, f"文档数量: {doc_count}", response_time=response_time)
            return True
        else:
            self.log_test("向量数据库统计", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_vector_db_health(self) -> bool:
        """测试向量数据库健康检查"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/vector-db/health")
        
        if error:
            self.log_test("向量数据库健康检查", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            healthy = data.get("healthy", False)
            self.log_test("向量数据库健康检查", True, f"健康状态: {healthy}", response_time=response_time)
            return True
        else:
            self.log_test("向量数据库健康检查", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_vector_db_collections(self) -> bool:
        """测试获取向量数据库集合"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/vector-db/collections")
        
        if error:
            self.log_test("获取向量数据库集合", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            collections = data.get("collections", [])
            self.log_test("获取向量数据库集合", True, f"集合数量: {len(collections)}", response_time=response_time)
            return True
        else:
            self.log_test("获取向量数据库集合", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_chat_api(self) -> bool:
        """测试聊天API"""
        response, response_time, error = self.make_request(
            "POST", 
            f"{self.api_prefix}/chat",
            json={"message": "省级竞赛一等奖加多少分", "chat_history": []},
            timeout=60
        )
        
        if error:
            self.log_test("聊天API", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            reply_len = len(str(data.get("data", {}).get("reply", "")))
            self.log_test("聊天API", True, f"回复长度: {reply_len}字符", response_time=response_time)
            return True
        else:
            self.log_test("聊天API", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_chat_cache_stats(self) -> bool:
        """测试聊天缓存统计"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/chat/cache/stats")
        
        if error:
            self.log_test("聊天缓存统计", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("聊天缓存统计", True, "缓存统计获取成功", response_time=response_time)
            return True
        else:
            self.log_test("聊天缓存统计", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_certificate_calculate(self) -> bool:
        """测试证书加分计算"""
        response, response_time, error = self.make_request(
            "POST",
            f"{self.api_prefix}/certificate/calculate",
            json={
                "certificate_text": "获得省级数学竞赛一等奖",
                "student_info": {"grade": "2023"}
            },
            timeout=60
        )
        
        if error:
            self.log_test("证书加分计算", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("证书加分计算", True, "计算成功", response_time=response_time)
            return True
        else:
            self.log_test("证书加分计算", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_certificate_analyze(self) -> bool:
        """测试证书分析"""
        response, response_time, error = self.make_request(
            "POST",
            f"{self.api_prefix}/certificate/analyze",
            json={
                "certificate_text": "全国大学生数学建模竞赛省级一等奖"
            },
            timeout=60
        )
        
        if error:
            self.log_test("证书分析", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("证书分析", True, "分析成功", response_time=response_time)
            return True
        else:
            self.log_test("证书分析", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_documents_list(self) -> bool:
        """测试文档列表"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/documents")
        
        if error:
            self.log_test("文档列表", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            docs = data.get("data", {}).get("documents", [])
            self.log_test("文档列表", True, f"文档数量: {len(docs)}", response_time=response_time)
            return True
        else:
            self.log_test("文档列表", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_prompts_list(self) -> bool:
        """测试Prompt列表"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/prompts")
        
        if error:
            self.log_test("Prompt列表", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            prompts = data.get("data", {}).get("prompts", [])
            self.log_test("Prompt列表", True, f"Prompt数量: {len(prompts)}", response_time=response_time)
            return True
        else:
            self.log_test("Prompt列表", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_prompts_get_system(self) -> bool:
        """测试获取系统Prompt"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/prompts/system")
        
        if error:
            self.log_test("获取系统Prompt", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("获取系统Prompt", True, "获取成功", response_time=response_time)
            return True
        else:
            self.log_test("获取系统Prompt", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_logs_levels(self) -> bool:
        """测试日志级别"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/logs/levels")
        
        if error:
            self.log_test("日志级别", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            levels = data.get("data", {}).get("levels", [])
            self.log_test("日志级别", True, f"级别数量: {len(levels)}", response_time=response_time)
            return True
        else:
            self.log_test("日志级别", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_logs_performance_summary(self) -> bool:
        """测试性能摘要"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/logs/performance/summary")
        
        if error:
            self.log_test("性能摘要", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("性能摘要", True, "获取成功", response_time=response_time)
            return True
        else:
            self.log_test("性能摘要", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_cache_stats(self) -> bool:
        """测试缓存统计"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/cache/stats")
        
        if error:
            self.log_test("缓存统计", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            caches = data.get("data", {}).get("caches", {})
            self.log_test("缓存统计", True, f"缓存数量: {len(caches)}", response_time=response_time)
            return True
        else:
            self.log_test("缓存统计", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def test_cache_health(self) -> bool:
        """测试缓存健康检查"""
        response, response_time, error = self.make_request("GET", f"{self.api_prefix}/cache/health")
        
        if error:
            self.log_test("缓存健康检查", False, error, response_time=response_time)
            return False
        
        if response.status_code == 200:
            data = response.json()
            healthy = data.get("healthy", False)
            self.log_test("缓存健康检查", True, f"健康状态: {healthy}", response_time=response_time)
            return True
        else:
            self.log_test("缓存健康检查", False, f"状态码: {response.status_code}", response_time=response_time)
            return False
    
    def run_all_tests(self, quick_mode: bool = False) -> Dict[str, Any]:
        """运行所有测试
        
        Args:
            quick_mode: 快速模式，仅测试核心功能
            
        Returns:
            测试结果摘要
        """
        print("=" * 70)
        print("RAG系统API完整测试")
        print(f"测试时间: {datetime.now().isoformat()}")
        print(f"服务地址: {self.base_url}")
        print(f"测试模式: {'快速测试' if quick_mode else '完整测试'}")
        print("=" * 70)
        print()
        
        print("--- 基础端点测试 ---")
        self.test_root_endpoint()
        self.test_health_check()
        
        print("--- 系统管理API测试 ---")
        self.test_system_info()
        self.test_system_health()
        self.test_system_config()
        self.test_llm_config()
        
        print("--- 向量数据库API测试 ---")
        self.test_vector_db_stats()
        self.test_vector_db_health()
        self.test_vector_db_collections()
        
        print("--- 聊天API测试 ---")
        self.test_chat_api()
        self.test_chat_cache_stats()
        
        print("--- 证书API测试 ---")
        self.test_certificate_calculate()
        self.test_certificate_analyze()
        
        print("--- 文档管理API测试 ---")
        self.test_documents_list()
        
        print("--- Prompt管理API测试 ---")
        self.test_prompts_list()
        self.test_prompts_get_system()
        
        print("--- 日志管理API测试 ---")
        self.test_logs_levels()
        self.test_logs_performance_summary()
        
        print("--- 缓存管理API测试 ---")
        self.test_cache_stats()
        self.test_cache_health()
        
        total = self.passed_count + self.failed_count
        pass_rate = (self.passed_count / total * 100) if total > 0 else 0
        
        print("=" * 70)
        print(f"测试完成: {self.passed_count}/{total} 通过 ({pass_rate:.1f}%)")
        print(f"  ✅ 通过: {self.passed_count}")
        print(f"  ❌ 失败: {self.failed_count}")
        print("=" * 70)
        
        return {
            "total": total,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "pass_rate": f"{pass_rate:.1f}%",
            "results": self.test_results,
            "test_time": datetime.now().isoformat(),
            "base_url": self.base_url
        }
    
    def save_results(self, filename: str = "test_results.json"):
        """保存测试结果到文件"""
        results_file = project_root / "tests" / filename
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "total": self.passed_count + self.failed_count,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "results": self.test_results,
                "test_time": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n测试结果已保存到: {results_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG系统API测试")
    parser.add_argument("--quick", action="store_true", help="快速测试模式")
    parser.add_argument("--save", action="store_true", help="保存测试结果")
    parser.add_argument("--url", default="http://localhost:8010", help="服务地址")
    
    args = parser.parse_args()
    
    tester = RAGAPITester(base_url=args.url)
    results = tester.run_all_tests(quick_mode=args.quick)
    
    if args.save:
        tester.save_results()
    
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
