#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面API和RAG系统测试脚本
测试所有后端API接口和RAG系统功能
"""
import requests
import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("APITester")


class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def record(self, category: str, test_name: str, success: bool, 
               response: Dict = None, error: str = None, duration_ms: int = 0,
               details: Dict = None):
        """记录测试结果"""
        result = {
            "category": category,
            "test_name": test_name,
            "success": success,
            "response": response,
            "error": error,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.results.append(result)
        
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"[{category}] {status}: {test_name} ({duration_ms}ms)")
        if error:
            logger.error(f"  错误: {error}")
        if details:
            logger.debug(f"  详情: {json.dumps(details, ensure_ascii=False)[:200]}")
            
    def get_summary(self) -> Dict:
        """获取测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0, "failed": 0}
            categories[cat]["total"] += 1
            if r["success"]:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
                
        return {
            "test_time": self.start_time.isoformat(),
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%",
            "categories": categories
        }


class VisualModelAPITester:
    """Visual Model后端API测试器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.token = None
        self.user_info = None
        
    def test_health(self, result: TestResult):
        """测试健康检查接口"""
        logger.info("=" * 60)
        logger.info("测试健康检查接口")
        logger.info("=" * 60)
        
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                result.record("健康检查", "健康检查端点", True, response.json(), duration_ms=duration)
            else:
                result.record("健康检查", "健康检查端点", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            result.record("健康检查", "健康检查端点", False, None, str(e))
            
    def test_auth_apis(self, result: TestResult):
        """测试认证API"""
        logger.info("=" * 60)
        logger.info("测试认证API")
        logger.info("=" * 60)
        
        # 测试管理员登录
        try:
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                result.record("认证API", "管理员登录", True, {"token": self.token[:20] + "..." if self.token else None}, duration_ms=duration)
            else:
                result.record("认证API", "管理员登录", False, None, f"状态码: {response.status_code}, {response.text}", duration)
        except Exception as e:
            result.record("认证API", "管理员登录", False, None, str(e))
            
        # 测试教师登录
        try:
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "teacher", "password": "teacher123"},
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            result.record("认证API", "教师登录", response.status_code == 200, 
                         response.json() if response.status_code == 200 else None,
                         None if response.status_code == 200 else f"状态码: {response.status_code}", duration)
        except Exception as e:
            result.record("认证API", "教师登录", False, None, str(e))
            
        # 测试学生登录
        try:
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "student_202300502128", "password": "student123"},
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            result.record("认证API", "学生登录", response.status_code == 200,
                         response.json() if response.status_code == 200 else None,
                         None if response.status_code == 200 else f"状态码: {response.status_code}", duration)
        except Exception as e:
            result.record("认证API", "学生登录", False, None, str(e))
            
        # 测试错误密码
        try:
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "admin", "password": "wrongpassword"},
                timeout=10
            )
            duration = int((time.time() - start) * 1000)
            result.record("认证API", "错误密码登录(应失败)", response.status_code == 401,
                         None, None, duration)
        except Exception as e:
            result.record("认证API", "错误密码登录", False, None, str(e))
            
        # 测试获取当前用户信息
        if self.token:
            try:
                start = time.time()
                response = requests.get(
                    f"{self.base_url}/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    self.user_info = response.json()
                    result.record("认证API", "获取当前用户信息", True, self.user_info, duration_ms=duration)
                else:
                    result.record("认证API", "获取当前用户信息", False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                result.record("认证API", "获取当前用户信息", False, None, str(e))
                
    def test_teacher_apis(self, result: TestResult):
        """测试教师API"""
        logger.info("=" * 60)
        logger.info("测试教师API")
        logger.info("=" * 60)
        
        if not self.token:
            logger.warning("跳过教师API测试: 未登录")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试获取学生列表
        endpoints = [
            ("/api/v1/teacher/students", "获取学生列表"),
            ("/api/v1/teacher/classes", "获取班级列表"),
            ("/api/v1/teacher/scores", "获取成绩列表"),
        ]
        
        for endpoint, name in endpoints:
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=10)
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 403, 404]:
                    result.record("教师API", name, True, 
                                 {"status_code": response.status_code, "data": response.json() if response.status_code == 200 else None},
                                 None, duration)
                else:
                    result.record("教师API", name, False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                result.record("教师API", name, False, None, str(e))
                
    def test_admin_apis(self, result: TestResult):
        """测试管理员API"""
        logger.info("=" * 60)
        logger.info("测试管理员API")
        logger.info("=" * 60)
        
        if not self.token:
            logger.warning("跳过管理员API测试: 未登录")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试管理员接口
        endpoints = [
            ("/api/v1/admin/users", "获取用户列表"),
            ("/api/v1/admin/settings", "获取系统设置"),
            ("/api/v1/admin/rules/list", "获取规则文档列表"),
        ]
        
        for endpoint, name in endpoints:
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=10)
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 403, 404]:
                    result.record("管理员API", name, True,
                                 {"status_code": response.status_code, "data": response.json() if response.status_code == 200 else None},
                                 None, duration)
                else:
                    result.record("管理员API", name, False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                result.record("管理员API", name, False, None, str(e))
                
    def test_student_apis(self, result: TestResult):
        """测试学生API"""
        logger.info("=" * 60)
        logger.info("测试学生API")
        logger.info("=" * 60)
        
        if not self.token:
            logger.warning("跳过学生API测试: 未登录")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试学生接口
        endpoints = [
            ("/api/v1/student/scores/summary", "获取成绩摘要"),
            ("/api/v1/student/uploads", "获取上传历史"),
        ]
        
        for endpoint, name in endpoints:
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=10)
                duration = int((time.time() - start) * 1000)
                
                if response.status_code in [200, 403, 404]:
                    result.record("学生API", name, True,
                                 {"status_code": response.status_code},
                                 None, duration)
                else:
                    result.record("学生API", name, False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                result.record("学生API", name, False, None, str(e))
                
    def test_ocr_apis(self, result: TestResult):
        """测试OCR API"""
        logger.info("=" * 60)
        logger.info("测试OCR API")
        logger.info("=" * 60)
        
        if not self.token:
            logger.warning("跳过OCR API测试: 未登录")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试OCR服务状态
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api/v1/ocr/status", headers=headers, timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code in [200, 404]:
                result.record("OCR API", "OCR服务状态", True,
                             {"status_code": response.status_code}, None, duration)
            else:
                result.record("OCR API", "OCR服务状态", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            result.record("OCR API", "OCR服务状态", False, None, str(e))
            
    def run_all_tests(self, result: TestResult):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info(f"开始测试Visual Model后端: {self.base_url}")
        logger.info("=" * 60)
        
        self.test_health(result)
        self.test_auth_apis(result)
        self.test_teacher_apis(result)
        self.test_admin_apis(result)
        self.test_student_apis(result)
        self.test_ocr_apis(result)


class RAGAPITester:
    """RAG后端API测试器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        
    def test_health(self, result: TestResult):
        """测试健康检查接口"""
        logger.info("=" * 60)
        logger.info("测试RAG健康检查接口")
        logger.info("=" * 60)
        
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                result.record("RAG健康检查", "RAG健康检查端点", True, response.json(), duration_ms=duration)
            else:
                result.record("RAG健康检查", "RAG健康检查端点", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            result.record("RAG健康检查", "RAG健康检查端点", False, None, str(e))
            
    def test_system_apis(self, result: TestResult):
        """测试系统API"""
        logger.info("=" * 60)
        logger.info("测试RAG系统API")
        logger.info("=" * 60)
        
        # 测试系统信息
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api/v1/system/info", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                result.record("RAG系统API", "获取系统信息", True, response.json(), duration_ms=duration)
            else:
                result.record("RAG系统API", "获取系统信息", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            result.record("RAG系统API", "获取系统信息", False, None, str(e))
            
    def test_chat_apis(self, result: TestResult):
        """测试聊天API"""
        logger.info("=" * 60)
        logger.info("测试RAG聊天API")
        logger.info("=" * 60)
        
        # 测试用例 - 基于综测计算细则
        test_cases = [
            {
                "name": "省级竞赛一等奖加分查询",
                "message": "省级竞赛一等奖加多少分",
                "expected_keywords": ["省级", "一等奖", "加分", "竞赛"]
            },
            {
                "name": "国家级竞赛加分查询",
                "message": "国家级A类竞赛一等奖加多少分",
                "expected_keywords": ["国家级", "A类", "一等奖"]
            },
            {
                "name": "蓝桥杯竞赛查询",
                "message": "蓝桥杯是什么级别的竞赛",
                "expected_keywords": ["蓝桥杯", "A类", "国家级"]
            },
            {
                "name": "挑战杯竞赛查询",
                "message": "挑战杯竞赛的级别是什么",
                "expected_keywords": ["挑战杯", "A类"]
            },
            {
                "name": "综合测评计算规则",
                "message": "综合测评总分怎么计算",
                "expected_keywords": ["综合测评", "计算", "总分"]
            }
        ]
        
        for tc in test_cases:
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/chat",
                    json={"message": tc["message"], "chat_history": []},
                    timeout=120
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    # 处理不同的响应格式
                    if data.get("success") and data.get("data"):
                        response_text = data["data"].get("response", "") or data["data"].get("answer", "")
                    else:
                        response_text = data.get("response", "") or data.get("answer", "") or str(data)
                    
                    # 检查关键词匹配
                    matched_keywords = []
                    for kw in tc["expected_keywords"]:
                        if kw in response_text:
                            matched_keywords.append(kw)
                    
                    keyword_match_rate = len(matched_keywords) / len(tc["expected_keywords"]) * 100 if tc["expected_keywords"] else 0
                    
                    result.record("RAG聊天API", tc["name"], True, 
                                 {"response": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                                  "matched_keywords": matched_keywords,
                                  "keyword_match_rate": f"{keyword_match_rate:.1f}%"},
                                 None, duration,
                                 {"expected_keywords": tc["expected_keywords"], "actual_keywords": matched_keywords})
                else:
                    result.record("RAG聊天API", tc["name"], False, None, f"状态码: {response.status_code}, {response.text[:200]}", duration)
            except Exception as e:
                result.record("RAG聊天API", tc["name"], False, None, str(e))
                
    def test_document_apis(self, result: TestResult):
        """测试文档API"""
        logger.info("=" * 60)
        logger.info("测试RAG文档API")
        logger.info("=" * 60)
        
        # 测试获取文档列表
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api/v1/documents", timeout=10)
            duration = int((time.time() - start) * 1000)
            
            if response.status_code in [200, 404]:
                result.record("RAG文档API", "获取文档列表", True,
                             response.json() if response.status_code == 200 else {"status": "not_found"},
                             None, duration)
            else:
                result.record("RAG文档API", "获取文档列表", False, None, f"状态码: {response.status_code}", duration)
        except Exception as e:
            result.record("RAG文档API", "获取文档列表", False, None, str(e))
            
    def run_all_tests(self, result: TestResult):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info(f"开始测试RAG后端: {self.base_url}")
        logger.info("=" * 60)
        
        self.test_health(result)
        self.test_system_apis(result)
        self.test_chat_apis(result)
        self.test_document_apis(result)


class RAGAccuracyEvaluator:
    """RAG检索准确性评估器"""
    
    def __init__(self, rag_url: str = "http://127.0.0.1:8000"):
        self.rag_url = rag_url
        
        # 基于学科竞赛名称列表的测试用例
        self.competition_tests = [
            {
                "query": "蓝桥杯是什么级别的竞赛",
                "expected_answer": "A类国家级竞赛",
                "expected_competition": "蓝桥杯",
                "expected_level": "国家级",
                "expected_category": "A"
            },
            {
                "query": "挑战杯大学生科技作品竞赛的级别",
                "expected_answer": "A类国家级竞赛",
                "expected_competition": "挑战杯",
                "expected_level": "国家级",
                "expected_category": "A"
            },
            {
                "query": "互联网+大学生创新创业大赛是什么级别",
                "expected_answer": "A类国家级竞赛",
                "expected_competition": "互联网+",
                "expected_level": "国家级",
                "expected_category": "A"
            },
            {
                "query": "全国大学生电子设计竞赛的类别",
                "expected_answer": "A类竞赛",
                "expected_competition": "电子设计竞赛",
                "expected_level": "国家级",
                "expected_category": "A"
            },
            {
                "query": "华为ICT大赛是什么级别",
                "expected_answer": "A类竞赛",
                "expected_competition": "华为ICT",
                "expected_level": "国家级",
                "expected_category": "A"
            }
        ]
        
    def evaluate(self, result: TestResult):
        """评估RAG检索准确性"""
        logger.info("=" * 60)
        logger.info("评估RAG检索准确性")
        logger.info("=" * 60)
        
        for test in self.competition_tests:
            try:
                start = time.time()
                response = requests.post(
                    f"{self.rag_url}/api/v1/chat",
                    json={"message": test["query"], "chat_history": []},
                    timeout=60
                )
                duration = int((time.time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "") or data.get("answer", "")
                    
                    # 评估准确性
                    competition_found = test["expected_competition"] in response_text
                    level_found = test["expected_level"] in response_text
                    category_found = test["expected_category"] in response_text
                    
                    accuracy_score = sum([competition_found, level_found, category_found]) / 3 * 100
                    
                    result.record("RAG准确性评估", f"查询: {test['query'][:20]}...", 
                                 accuracy_score >= 50,
                                 {"response": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                                  "accuracy_score": f"{accuracy_score:.1f}%",
                                  "competition_found": competition_found,
                                  "level_found": level_found,
                                  "category_found": category_found},
                                 None, duration)
                else:
                    result.record("RAG准确性评估", f"查询: {test['query'][:20]}...", 
                                 False, None, f"状态码: {response.status_code}", duration)
            except Exception as e:
                result.record("RAG准确性评估", f"查询: {test['query'][:20]}...", 
                             False, None, str(e))


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始全面API和RAG系统测试")
    logger.info(f"测试时间: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    result = TestResult()
    
    # 测试Visual Model后端
    visual_tester = VisualModelAPITester()
    visual_tester.run_all_tests(result)
    
    # 测试RAG后端
    rag_tester = RAGAPITester()
    rag_tester.run_all_tests(result)
    
    # 评估RAG准确性
    rag_evaluator = RAGAccuracyEvaluator()
    rag_evaluator.evaluate(result)
    
    # 生成报告
    summary = result.get_summary()
    
    logger.info("=" * 60)
    logger.info("测试报告")
    logger.info("=" * 60)
    logger.info(f"总计: {summary['total']} 个测试")
    logger.info(f"通过: {summary['passed']} 个")
    logger.info(f"失败: {summary['failed']} 个")
    logger.info(f"通过率: {summary['pass_rate']}")
    
    for cat, stats in summary['categories'].items():
        logger.info(f"  [{cat}] 通过: {stats['passed']}/{stats['total']}")
    
    # 保存报告
    report = {
        "summary": summary,
        "results": result.results
    }
    
    with open("full_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    logger.info(f"\n测试报告已保存到: full_test_report.json")
    
    return report


if __name__ == "__main__":
    main()
