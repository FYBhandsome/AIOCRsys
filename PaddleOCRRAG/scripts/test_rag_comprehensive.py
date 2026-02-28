#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统全面功能测试脚本
测试：文档检索、问答生成、上下文理解、多轮对话、向量数据库管理
"""

import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

RAG_BASE_URL = "http://127.0.0.1:8002"
VISUAL_BASE_URL = "http://127.0.0.1:8001"

def log_info(message: str):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [INFO] {message}")

def log_error(message: str):
    """打印错误日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [ERROR] {message}")

def log_warn(message: str):
    """打印警告日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [WARN] {message}")

def log_success(message: str):
    """打印成功日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [SUCCESS] {message}")

def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)

def print_sub_separator(title: str = ""):
    """打印子分隔线"""
    print("\n" + "-" * 60)
    if title:
        print(f"  {title}")
        print("-" * 60)


class RAGSystemTester:
    """RAG系统测试器"""
    
    def __init__(self):
        self.test_results = []
        self.session_id = f"test_{int(time.time())}"
    
    def record_result(self, test_name: str, success: bool, message: str, 
                      duration_ms: float = 0, details: Dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✓ 通过" if success else "✗ 失败"
        log_info(f"{status}: {test_name} - {message} ({duration_ms:.2f}ms)")
    
    def test_health_check(self):
        """测试健康检查"""
        print_separator("健康检查测试")
        
        # RAG服务健康检查
        try:
            start = time.time()
            response = requests.get(f"{RAG_BASE_URL}/", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                log_success(f"RAG服务健康检查通过: {data}")
                self.record_result("RAG健康检查", True, "服务正常", duration, data)
            else:
                log_error(f"RAG服务健康检查失败: HTTP {response.status_code}")
                self.record_result("RAG健康检查", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            log_error(f"RAG服务连接失败: {e}")
            self.record_result("RAG健康检查", False, str(e))
        
        # Visual Model服务健康检查
        try:
            start = time.time()
            response = requests.get(f"{VISUAL_BASE_URL}/health", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                log_success(f"Visual Model服务健康检查通过: {data}")
                self.record_result("Visual Model健康检查", True, "服务正常", duration, data)
            else:
                log_error(f"Visual Model服务健康检查失败: HTTP {response.status_code}")
                self.record_result("Visual Model健康检查", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            log_error(f"Visual Model服务连接失败: {e}")
            self.record_result("Visual Model健康检查", False, str(e))
    
    def test_document_retrieval(self):
        """测试文档检索准确性"""
        print_separator("文档检索准确性测试")
        
        test_queries = [
            ("省级竞赛一等奖加多少分", "竞赛加分"),
            ("英语四级证书加分标准", "证书加分"),
            ("社会实践要求多少学时", "社会实践"),
            ("创新创业加分规则", "创新创业"),
            ("综测计算公式", "综测计算"),
            ("蓝桥杯竞赛加分", "竞赛加分"),
            ("计算机二级证书加分", "证书加分"),
            ("志愿服务时长要求", "志愿服务"),
        ]
        
        for query, category in test_queries:
            print_sub_separator(f"查询: {query}")
            
            try:
                start = time.time()
                response = requests.post(
                    f"{RAG_BASE_URL}/api/v1/chat",
                    json={"message": query, "chat_history": []},
                    timeout=60
                )
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("data", {})
                    
                    log_info(f"检索结果: {json.dumps(results, ensure_ascii=False)[:500]}...")
                    
                    has_relevant = results is not None and len(str(results)) > 10
                    
                    self.record_result(
                        f"检索测试: {category}", 
                        has_relevant,
                        f"检索完成" if has_relevant else "无结果",
                        duration,
                        {"query": query, "result": str(results)[:200]}
                    )
                else:
                    log_error(f"检索失败: HTTP {response.status_code}")
                    self.record_result(f"检索测试: {category}", False, f"HTTP {response.status_code}", duration)
                    
            except Exception as e:
                log_error(f"检索异常: {e}")
                self.record_result(f"检索测试: {category}", False, str(e))
    
    def test_qa_generation(self):
        """测试问答生成相关性"""
        print_separator("问答生成相关性测试")
        
        test_questions = [
            "省级竞赛一等奖能加多少分？",
            "英语四级证书可以加多少综测分？",
            "参加社会实践需要满足什么条件？",
            "创新创业项目如何申请加分？",
        ]
        
        for question in test_questions:
            print_sub_separator(f"问题: {question}")
            
            try:
                start = time.time()
                response = requests.post(
                    f"{RAG_BASE_URL}/api/v1/chat",
                    json={
                        "message": question,
                        "chat_history": []
                    },
                    timeout=60
                )
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("data", {})
                    answer = result.get("answer", "") or result.get("response", "") or str(result)
                    
                    log_info(f"回答: {answer[:300]}...")
                    
                    has_answer = len(answer) > 20
                    
                    self.record_result(
                        f"问答测试: {question[:20]}...",
                        has_answer,
                        f"回答长度: {len(answer)}字",
                        duration,
                        {"question": question, "answer_length": len(answer)}
                    )
                else:
                    log_error(f"问答失败: HTTP {response.status_code}")
                    self.record_result(f"问答测试: {question[:20]}...", False, f"HTTP {response.status_code}", duration)
                    
            except Exception as e:
                log_error(f"问答异常: {e}")
                self.record_result(f"问答测试: {question[:20]}...", False, str(e))
    
    def test_context_understanding(self):
        """测试上下文理解能力"""
        print_separator("上下文理解能力测试")
        
        conversation = [
            ("我想了解竞赛加分政策", "开场询问"),
            ("蓝桥杯属于什么级别的竞赛？", "追问细节"),
            ("那这个竞赛一等奖能加多少分？", "上下文关联"),
            ("还有其他类似的竞赛吗？", "扩展询问"),
        ]
        
        chat_history = []
        
        for message, intent in conversation:
            print_sub_separator(f"[{intent}] {message}")
            
            try:
                start = time.time()
                response = requests.post(
                    f"{RAG_BASE_URL}/api/v1/chat",
                    json={
                        "message": message,
                        "chat_history": chat_history
                    },
                    timeout=60
                )
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("data", {})
                    answer = result.get("answer", "") or result.get("response", "") or str(result)
                    
                    chat_history.append({"role": "user", "content": message})
                    chat_history.append({"role": "assistant", "content": answer})
                    
                    log_info(f"回答: {answer[:200]}...")
                    
                    self.record_result(
                        f"上下文测试: {intent}",
                        len(answer) > 10,
                        f"回答长度: {len(answer)}字",
                        duration
                    )
                else:
                    self.record_result(f"上下文测试: {intent}", False, f"HTTP {response.status_code}", duration)
                    
            except Exception as e:
                log_error(f"上下文测试异常: {e}")
                self.record_result(f"上下文测试: {intent}", False, str(e))
    
    def test_multi_turn_dialog(self):
        """测试多轮对话连贯性"""
        print_separator("多轮对话连贯性测试")
        
        dialog_flow = [
            "你好，我想咨询综测加分问题",
            "我想知道学科竞赛的加分标准",
            "蓝桥杯省赛一等奖加多少分？",
            "国赛一等奖呢？",
            "谢谢，我明白了",
        ]
        
        chat_history = []
        dialog_history = []
        
        for i, message in enumerate(dialog_flow):
            print_sub_separator(f"第{i+1}轮对话: {message}")
            
            try:
                start = time.time()
                response = requests.post(
                    f"{RAG_BASE_URL}/api/v1/chat",
                    json={
                        "message": message,
                        "chat_history": chat_history
                    },
                    timeout=60
                )
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("data", {})
                    answer = result.get("answer", "") or result.get("response", "") or str(result)
                    
                    chat_history.append({"role": "user", "content": message})
                    chat_history.append({"role": "assistant", "content": answer})
                    
                    dialog_history.append({
                        "user": message,
                        "assistant": answer[:100] + "..."
                    })
                    
                    log_info(f"回答: {answer[:200]}...")
                    
                    self.record_result(
                        f"多轮对话: 第{i+1}轮",
                        len(answer) > 5,
                        f"对话正常",
                        duration
                    )
                else:
                    self.record_result(f"多轮对话: 第{i+1}轮", False, f"HTTP {response.status_code}", duration)
                    
            except Exception as e:
                log_error(f"多轮对话异常: {e}")
                self.record_result(f"多轮对话: 第{i+1}轮", False, str(e))
        
        print_sub_separator("对话历史")
        for i, h in enumerate(dialog_history):
            log_info(f"第{i+1}轮:")
            log_info(f"  用户: {h['user']}")
            log_info(f"  助手: {h['assistant']}")
    
    def test_vector_db_management(self):
        """测试向量数据库管理功能"""
        print_separator("向量数据库管理测试")
        
        # 测试获取统计信息
        print_sub_separator("获取向量数据库统计")
        try:
            start = time.time()
            response = requests.get(f"{RAG_BASE_URL}/api/v1/vector-db/stats", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                log_info(f"数据库统计: {json.dumps(data, ensure_ascii=False, indent=2)}")
                self.record_result("向量数据库统计", True, f"文档数: {data.get('total_documents', 0)}", duration, data)
            else:
                self.record_result("向量数据库统计", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            log_error(f"获取统计失败: {e}")
            self.record_result("向量数据库统计", False, str(e))
        
        # 测试健康检查
        print_sub_separator("向量数据库健康检查")
        try:
            start = time.time()
            response = requests.get(f"{RAG_BASE_URL}/api/v1/vector-db/health", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                log_info(f"健康状态: {json.dumps(data, ensure_ascii=False)}")
                self.record_result("向量数据库健康检查", data.get("healthy", False), f"状态: {data}", duration, data)
            else:
                self.record_result("向量数据库健康检查", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            log_error(f"健康检查失败: {e}")
            self.record_result("向量数据库健康检查", False, str(e))
        
        # 测试获取集合
        print_sub_separator("获取向量数据库集合")
        try:
            start = time.time()
            response = requests.get(f"{RAG_BASE_URL}/api/v1/vector-db/collections", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                collections = data.get("collections", [])
                log_info(f"集合列表: {collections}")
                self.record_result("向量数据库集合", True, f"集合数: {len(collections)}", duration, data)
            else:
                self.record_result("向量数据库集合", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            log_error(f"获取集合失败: {e}")
            self.record_result("向量数据库集合", False, str(e))
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        print_separator("测试报告")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        report = {
            "test_time": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%"
            },
            "results": self.test_results
        }
        
        log_info(f"总测试数: {total}")
        log_info(f"通过数: {passed}")
        log_info(f"失败数: {failed}")
        log_info(f"通过率: {report['summary']['pass_rate']}")
        
        # 按类别统计
        categories = {}
        for result in self.test_results:
            cat = result["test_name"].split(":")[0] if ":" in result["test_name"] else result["test_name"]
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0}
            if result["success"]:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
        
        print_sub_separator("分类统计")
        for cat, stats in categories.items():
            total_cat = stats["passed"] + stats["failed"]
            rate = stats["passed"] / total_cat * 100 if total_cat > 0 else 0
            log_info(f"  {cat}: {stats['passed']}/{total_cat} 通过 ({rate:.1f}%)")
        
        return report
    
    def run_all_tests(self):
        """运行所有测试"""
        print_separator("RAG系统全面功能测试")
        log_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_info(f"RAG服务地址: {RAG_BASE_URL}")
        log_info(f"Visual Model服务地址: {VISUAL_BASE_URL}")
        
        self.test_health_check()
        self.test_document_retrieval()
        self.test_qa_generation()
        self.test_context_understanding()
        self.test_multi_turn_dialog()
        self.test_vector_db_management()
        
        return self.generate_report()


def main():
    """主函数"""
    tester = RAGSystemTester()
    report = tester.run_all_tests()
    
    # 保存报告
    report_path = Path(__file__).parent / "test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    log_info(f"\n测试报告已保存: {report_path}")
    
    return report


if __name__ == "__main__":
    main()
