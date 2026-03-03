#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG检索准确性测试文件
功能：
1. 从RAG知识库检索信息并完整打印输出
2. 读取指定文档（docx和xlsx）的全部内容
3. 设计系统性比对方法验证检索准确性
4. 提供RAG系统优化建议
"""

import os
import sys
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DOCX_PATH = r"D:\PaddleOCR\PaddleOCRRAG\data\rules\03、计算机学院综合测评实施细则（2025）.docx"
XLSX_PATH = r"D:\PaddleOCR\PaddleOCRRAG\data\rules\05、学科竞赛名称列表.xlsx"


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    success: bool
    message: str
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AccuracyIssue:
    """准确性问题数据类"""
    issue_type: str
    query: str
    expected: str
    actual: str
    severity: str
    suggestion: str


@dataclass
class CompetitionRecord:
    """竞赛记录数据类"""
    name: str
    competition_type: str
    level: str
    row_index: int


class RAGAccuracyTester:
    """RAG检索准确性测试器"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.accuracy_issues: List[AccuracyIssue] = []
        self.competition_records: List[CompetitionRecord] = []
        self.docx_content: str = ""
        self.docx_paragraphs: List[str] = []
        self.performance_stats: Dict[str, List[float]] = {}
        
    def log_info(self, message: str):
        """打印信息日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [INFO] {message}")
    
    def log_error(self, message: str):
        """打印错误日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [ERROR] {message}")
    
    def log_warn(self, message: str):
        """打印警告日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [WARN] {message}")
    
    def log_success(self, message: str):
        """打印成功日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [SUCCESS] {message}")
    
    def print_separator(self, title: str = ""):
        """打印分隔线"""
        print("\n" + "=" * 80)
        if title:
            print(f"  {title}")
            print("=" * 80)
    
    def print_sub_separator(self, title: str = ""):
        """打印子分隔线"""
        print("\n" + "-" * 60)
        if title:
            print(f"  {title}")
            print("-" * 60)
    
    def record_result(self, test_name: str, success: bool, message: str,
                      duration_ms: float = 0, details: Dict = None):
        """记录测试结果"""
        result = TestResult(
            test_name=test_name,
            success=success,
            message=message,
            duration_ms=duration_ms,
            details=details or {}
        )
        self.test_results.append(result)
        
        status = "✓ 通过" if success else "✗ 失败"
        self.log_info(f"{status}: {test_name} - {message} ({duration_ms:.2f}ms)")
    
    def record_issue(self, issue_type: str, query: str, expected: str,
                     actual: str, severity: str, suggestion: str):
        """记录准确性问题"""
        issue = AccuracyIssue(
            issue_type=issue_type,
            query=query,
            expected=expected,
            actual=actual,
            severity=severity,
            suggestion=suggestion
        )
        self.accuracy_issues.append(issue)
        self.log_warn(f"发现问题 [{severity}]: {issue_type} - {query}")
    
    def record_performance(self, operation: str, duration_ms: float):
        """记录性能数据"""
        if operation not in self.performance_stats:
            self.performance_stats[operation] = []
        self.performance_stats[operation].append(duration_ms)
    
    def read_docx_document(self, file_path: str) -> Tuple[bool, str]:
        """读取docx文档内容"""
        self.print_separator(f"读取docx文档: {Path(file_path).name}")
        start_time = time.time()
        
        try:
            if not os.path.exists(file_path):
                self.log_error(f"文件不存在: {file_path}")
                return False, ""
            
            try:
                from docx import Document
                doc = Document(file_path)
                
                self.docx_paragraphs = []
                for para in doc.paragraphs:
                    text = para.text.strip()
                    if text:
                        self.docx_paragraphs.append(text)
                
                self.docx_content = "\n".join(self.docx_paragraphs)
                
                duration_ms = (time.time() - start_time) * 1000
                self.log_success(f"使用python-docx读取成功: {len(self.docx_paragraphs)}个段落")
                self.log_info(f"文档总字符数: {len(self.docx_content)}")
                self.record_performance("docx_read", duration_ms)
                self.record_result("读取docx文档", True, f"读取{len(self.docx_paragraphs)}个段落", duration_ms)
                
                self._print_docx_summary()
                return True, self.docx_content
                
            except ImportError:
                self.log_warn("python-docx未安装，尝试使用docx2txt")
                
                try:
                    import docx2txt
                    self.docx_content = docx2txt.process(file_path)
                    self.docx_paragraphs = [p.strip() for p in self.docx_content.split('\n') if p.strip()]
                    
                    duration_ms = (time.time() - start_time) * 1000
                    self.log_success(f"使用docx2txt读取成功: {len(self.docx_paragraphs)}个段落")
                    self.log_info(f"文档总字符数: {len(self.docx_content)}")
                    self.record_performance("docx_read", duration_ms)
                    self.record_result("读取docx文档", True, f"读取{len(self.docx_paragraphs)}个段落", duration_ms)
                    
                    self._print_docx_summary()
                    return True, self.docx_content
                    
                except ImportError:
                    self.log_error("docx2txt也未安装，无法读取docx文件")
                    self.record_result("读取docx文档", False, "缺少docx解析库")
                    return False, ""
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_error(f"读取docx文档失败: {e}")
            self.record_result("读取docx文档", False, str(e), duration_ms)
            return False, ""
    
    def _print_docx_summary(self):
        """打印docx文档摘要"""
        self.print_sub_separator("文档内容摘要")
        
        self.log_info("前10个段落预览:")
        for i, para in enumerate(self.docx_paragraphs[:10]):
            preview = para[:80] + "..." if len(para) > 80 else para
            print(f"  [{i+1}] {preview}")
        
        key_sections = self._extract_key_sections()
        if key_sections:
            self.print_sub_separator("关键章节识别")
            for section, content in key_sections.items():
                preview = content[:100] + "..." if len(content) > 100 else content
                self.log_info(f"  {section}: {preview}")
    
    def _extract_key_sections(self) -> Dict[str, str]:
        """提取关键章节"""
        sections = {}
        section_patterns = [
            (r'第[一二三四五六七八九十]+[章节部分]\s*(.+?)(?=\n|$)', '章节标题'),
            (r'([一二三四五六七八九十]+)[、.．]\s*(.+?)(?=\n|$)', '编号标题'),
            (r'(\d+)[、.．]\s*(.+?)(?=\n|$)', '数字编号'),
        ]
        
        current_section = None
        current_content = []
        
        for para in self.docx_paragraphs:
            is_section_start = False
            for pattern, _ in section_patterns:
                match = re.search(pattern, para)
                if match:
                    if current_section and current_content:
                        sections[current_section] = "\n".join(current_content)
                    current_section = para[:50]
                    current_content = [para]
                    is_section_start = True
                    break
            
            if not is_section_start and current_section:
                current_content.append(para)
        
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        
        return sections
    
    def read_xlsx_document(self, file_path: str) -> Tuple[bool, List[CompetitionRecord]]:
        """读取xlsx文档内容"""
        self.print_separator(f"读取xlsx文档: {Path(file_path).name}")
        start_time = time.time()
        
        try:
            if not os.path.exists(file_path):
                self.log_error(f"文件不存在: {file_path}")
                return False, []
            
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            
            self.log_info(f"工作表名称: {sheet.title}")
            self.log_info(f"数据范围: {sheet.dimensions}")
            
            header_row = None
            for row_idx, row in enumerate(sheet.iter_rows(max_row=10), 1):
                cell_values = [str(cell.value) if cell.value else "" for cell in row]
                if '竞赛名称' in ' '.join(cell_values) or '竞赛类别' in ' '.join(cell_values):
                    header_row = row_idx
                    break
            
            if header_row is None:
                header_row = 3
            
            self.log_info(f"表头行识别: 第{header_row}行")
            
            headers = []
            for col_idx, cell in enumerate(sheet[header_row], 1):
                headers.append(str(cell.value).strip() if cell.value else f"列{col_idx}")
            
            self.log_info(f"表头: {headers}")
            
            self.competition_records = []
            
            for row_idx, row in enumerate(sheet.iter_rows(min_row=header_row + 1), header_row + 1):
                values = [str(cell.value).strip() if cell.value else "" for cell in row]
                
                if len(values) >= 4 and values[1] and values[1] != 'nan':
                    record = CompetitionRecord(
                        name=values[1],
                        competition_type=values[2] if len(values) > 2 else "",
                        level=values[3] if len(values) > 3 else "",
                        row_index=row_idx
                    )
                    self.competition_records.append(record)
            
            wb.close()
            
            duration_ms = (time.time() - start_time) * 1000
            self.log_success(f"读取成功: {len(self.competition_records)}条竞赛记录")
            self.record_performance("xlsx_read", duration_ms)
            self.record_result("读取xlsx文档", True, f"读取{len(self.competition_records)}条记录", duration_ms)
            
            self._print_xlsx_summary()
            return True, self.competition_records
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_error(f"读取xlsx文档失败: {e}")
            self.record_result("读取xlsx文档", False, str(e), duration_ms)
            return False, []
    
    def _print_xlsx_summary(self):
        """打印xlsx文档摘要"""
        self.print_sub_separator("竞赛列表统计")
        
        type_stats = {}
        level_stats = {}
        
        for record in self.competition_records:
            comp_type = record.competition_type or "未知"
            level = record.level or "未知"
            type_stats[comp_type] = type_stats.get(comp_type, 0) + 1
            level_stats[level] = level_stats.get(level, 0) + 1
        
        self.log_info("按类别统计:")
        for comp_type, count in sorted(type_stats.items()):
            self.log_info(f"  {comp_type}: {count}条")
        
        self.log_info("按级别统计:")
        for level, count in sorted(level_stats.items()):
            self.log_info(f"  {level}: {count}条")
        
        self.print_sub_separator("部分竞赛记录预览")
        for i, record in enumerate(self.competition_records[:10]):
            self.log_info(f"  [{record.row_index}] {record.name[:40]} | {record.competition_type} | {record.level}")
    
    def init_rag_system(self) -> bool:
        """初始化RAG系统"""
        self.print_separator("初始化RAG系统")
        start_time = time.time()
        
        try:
            from app.rag import get_vector_db, get_competition_mapper
            
            self.vector_db = get_vector_db()
            self.competition_mapper = get_competition_mapper()
            
            duration_ms = (time.time() - start_time) * 1000
            self.log_success("RAG系统初始化成功")
            self.record_performance("rag_init", duration_ms)
            self.record_result("初始化RAG系统", True, "初始化完成", duration_ms)
            
            stats = self.vector_db.get_category_stats()
            self.log_info(f"向量数据库统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
            
            return True
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_error(f"RAG系统初始化失败: {e}")
            self.record_result("初始化RAG系统", False, str(e), duration_ms)
            return False
    
    def search_and_print(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """执行检索并打印完整结果"""
        self.print_sub_separator(f"检索查询: {query}")
        start_time = time.time()
        
        try:
            results = self.vector_db.search_relevant(
                query=query,
                top_k=top_k
            )
            
            duration_ms = (time.time() - start_time) * 1000
            self.record_performance("rag_search", duration_ms)
            
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            distances = results.get("distances", [])
            
            self.log_info(f"检索耗时: {duration_ms:.2f}ms")
            self.log_info(f"返回文档数: {len(documents)}")
            
            print("\n" + "=" * 70)
            print("  完整检索结果")
            print("=" * 70)
            
            for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
                similarity = 1 / (1 + dist)
                print(f"\n[结果 {i}] 相似度: {similarity:.4f} (距离: {dist:.4f})")
                print("-" * 70)
                print(f"元数据: {json.dumps(meta, ensure_ascii=False)}")
                print("-" * 70)
                print(f"文档内容:\n{doc[:500]}{'...' if len(doc) > 500 else ''}")
                print("-" * 70)
            
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_error(f"检索失败: {e}")
            self.record_result("RAG检索", False, str(e), duration_ms)
            return {}
    
    def search_with_category_awareness(self, query: str, top_k: int = 5) -> Tuple[List, Any]:
        """执行类别感知检索"""
        self.print_sub_separator(f"类别感知检索: {query}")
        start_time = time.time()
        
        try:
            results, intent = self.vector_db.search_with_category_awareness(
                query=query,
                top_k=top_k
            )
            
            duration_ms = (time.time() - start_time) * 1000
            self.record_performance("category_aware_search", duration_ms)
            
            self.log_info(f"检索耗时: {duration_ms:.2f}ms")
            self.log_info(f"意图识别结果: {json.dumps(intent.to_dict(), ensure_ascii=False)}")
            self.log_info(f"返回结果数: {len(results)}")
            
            print("\n" + "=" * 70)
            print("  类别感知检索结果")
            print("=" * 70)
            
            for i, result in enumerate(results, 1):
                print(f"\n[结果 {i}] 重排分数: {result.reranked_score:.4f}")
                print("-" * 70)
                print(f"元数据: {json.dumps(result.metadata, ensure_ascii=False)}")
                print("-" * 70)
                print(f"文档内容:\n{result.document[:500]}{'...' if len(result.document) > 500 else ''}")
                print("-" * 70)
            
            return results, intent
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_error(f"类别感知检索失败: {e}")
            return [], None
    
    def verify_competition_category(self) -> Dict[str, Any]:
        """验证竞赛类别匹配准确性"""
        self.print_separator("竞赛类别匹配验证")
        start_time = time.time()
        
        test_cases = []
        correct_count = 0
        total_count = 0
        
        sample_competitions = [
            ("蓝桥杯国赛", "A", "国家级"),
            ("电子设计竞赛国赛", "A", "国家级"),
            ("数学建模国赛", "A", "国家级"),
            ("英语竞赛", "B", "国家级"),
            ("力学竞赛省赛", "A", "省部级"),
        ]
        
        for comp_name, expected_type, expected_level in sample_competitions:
            total_count += 1
            
            std_name, comp_info, match_score = self.competition_mapper.normalize_name(comp_name)
            
            if comp_info:
                actual_type = comp_info.competition_type
                actual_level = comp_info.level
                
                type_match = actual_type == expected_type
                level_match = actual_level == expected_level
                
                if type_match and level_match:
                    correct_count += 1
                    status = "✓ 正确"
                else:
                    status = "✗ 错误"
                    self.record_issue(
                        issue_type="竞赛类别不匹配",
                        query=comp_name,
                        expected=f"类别:{expected_type}, 级别:{expected_level}",
                        actual=f"类别:{actual_type}, 级别:{actual_level}",
                        severity="高" if not type_match else "中",
                        suggestion="检查竞赛映射表配置"
                    )
                
                test_cases.append({
                    "name": comp_name,
                    "standard_name": std_name,
                    "expected_type": expected_type,
                    "actual_type": actual_type,
                    "expected_level": expected_level,
                    "actual_level": actual_level,
                    "match_score": match_score,
                    "status": status
                })
                
                self.log_info(f"{status}: {comp_name}")
                self.log_info(f"  标准名称: {std_name}")
                self.log_info(f"  类别: 期望={expected_type}, 实际={actual_type}")
                self.log_info(f"  级别: 期望={expected_level}, 实际={actual_level}")
                self.log_info(f"  匹配分数: {match_score}")
            else:
                test_cases.append({
                    "name": comp_name,
                    "status": "✗ 未找到"
                })
                self.log_warn(f"未找到竞赛: {comp_name}")
        
        duration_ms = (time.time() - start_time) * 1000
        accuracy = correct_count / total_count * 100 if total_count > 0 else 0
        
        self.log_info(f"\n竞赛类别验证完成: {correct_count}/{total_count} 正确 ({accuracy:.1f}%)")
        self.record_result("竞赛类别验证", accuracy >= 80, f"准确率: {accuracy:.1f}%", duration_ms)
        
        return {
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_count": total_count,
            "test_cases": test_cases
        }
    
    def verify_score_rules(self) -> Dict[str, Any]:
        """验证分数规则准确性"""
        self.print_separator("分数规则验证")
        start_time = time.time()
        
        test_queries = [
            {
                "query": "A类竞赛国家级一等奖加多少分",
                "expected_keywords": ["30", "竞赛类型:A", "国家级", "一等奖"],
                "expected_metadata": {"competition_type": "A", "level": "国家级"},
                "category": "C1",
                "metadata_filter": None,
                "search_rules": True
            },
            {
                "query": "B类竞赛省部级二等奖加分",
                "expected_keywords": ["10", "B类", "省级", "二等奖"],
                "expected_metadata": {"competition_type": "B", "level": "省部级"},
                "category": "C1",
                "metadata_filter": None,
                "search_rules": True,
                "rule_query": "B类 省级 二等奖 分数表"
            },
            {
                "query": "英语四级证书加分",
                "expected_keywords": ["10", "四级", "英语"],
                "expected_metadata": {"certificate_type": "CET4"},
                "category": "C3",
                "metadata_filter": {"sub_category": "C3"},
                "search_rules": False
            },
            {
                "query": "计算机二级证书加分",
                "expected_keywords": ["5", "计算机二级"],
                "expected_metadata": {"certificate_type": "NCRE2"},
                "category": "C3",
                "metadata_filter": {"sub_category": "C3"},
                "search_rules": False
            },
        ]
        
        results = []
        
        for test_case in test_queries:
            query = test_case["query"]
            expected_keywords = test_case["expected_keywords"]
            metadata_filter = test_case.get("metadata_filter")
            search_rules = test_case.get("search_rules", False)
            
            self.print_sub_separator(f"验证: {query}")
            
            rag_results = self.vector_db.search_relevant(
                query=query, 
                top_k=10,
                metadata_filter=metadata_filter,
                similarity_threshold=0.5
            )
            documents = rag_results.get("documents", [])
            metadatas = rag_results.get("metadatas", [])
            
            if search_rules:
                rule_query = test_case.get("rule_query", f"分数表 {query}")
                rule_results = self.vector_db.search_relevant(
                    query=rule_query,
                    top_k=5,
                    metadata_filter={"type": "rule"},
                    similarity_threshold=0.3
                )
                documents.extend(rule_results.get("documents", []))
                metadatas.extend(rule_results.get("metadatas", []))
            
            if documents:
                combined_text = " ".join(documents).lower()
                found_keywords = []
                missing_keywords = []
                
                for kw in expected_keywords:
                    kw_variants = [kw.lower()]
                    if kw == "省部级":
                        kw_variants.append("省级")
                    elif kw == "省级":
                        kw_variants.append("省部级")
                    
                    found = any(variant in combined_text for variant in kw_variants)
                    if found:
                        found_keywords.append(kw)
                    else:
                        missing_keywords.append(kw)
                
                if metadatas:
                    for meta in metadatas:
                        if meta.get("score"):
                            score_val = str(meta.get("score"))
                            if score_val not in found_keywords and score_val in [kw for kw in expected_keywords if kw.isdigit()]:
                                found_keywords.append(score_val)
                                if score_val in missing_keywords:
                                    missing_keywords.remove(score_val)
                
                accuracy = len(found_keywords) / len(expected_keywords) * 100
                
                result = {
                    "query": query,
                    "expected_keywords": expected_keywords,
                    "found_keywords": found_keywords,
                    "missing_keywords": missing_keywords,
                    "accuracy": accuracy,
                    "status": "✓ 通过" if accuracy >= 75 else "✗ 失败"
                }
                
                if accuracy < 75:
                    self.record_issue(
                        issue_type="分数规则不完整",
                        query=query,
                        expected=", ".join(expected_keywords),
                        actual=f"找到: {', '.join(found_keywords)}",
                        severity="高",
                        suggestion="检查向量切片是否包含完整分数信息"
                    )
                
                self.log_info(f"期望关键词: {expected_keywords}")
                self.log_info(f"找到关键词: {found_keywords}")
                self.log_info(f"缺失关键词: {missing_keywords}")
                self.log_info(f"准确率: {accuracy:.1f}%")
                
                results.append(result)
            else:
                results.append({
                    "query": query,
                    "status": "✗ 无结果"
                })
                self.record_issue(
                    issue_type="检索无结果",
                    query=query,
                    expected="有相关结果",
                    actual="无结果",
                    severity="高",
                    suggestion="检查文档是否已正确向量化"
                )
        
        duration_ms = (time.time() - start_time) * 1000
        avg_accuracy = sum(r.get("accuracy", 0) for r in results) / len(results) if results else 0
        
        self.log_info(f"\n分数规则验证完成: 平均准确率 {avg_accuracy:.1f}%")
        self.record_result("分数规则验证", avg_accuracy >= 70, f"平均准确率: {avg_accuracy:.1f}%", duration_ms)
        
        return {
            "average_accuracy": avg_accuracy,
            "results": results
        }
    
    def verify_comprehensive_evaluation_rules(self) -> Dict[str, Any]:
        """验证综合测评规则完整性"""
        self.print_separator("综合测评规则验证")
        start_time = time.time()
        
        key_rules = [
            "学习成绩占比",
            "思想品德",
            "身体素质",
            "创新创业",
            "社会实践",
            "志愿服务",
            "竞赛加分上限",
            "证书加分上限",
        ]
        
        results = []
        
        for rule_topic in key_rules:
            self.print_sub_separator(f"验证规则: {rule_topic}")
            
            query = f"综合测评{rule_topic}"
            rag_results = self.vector_db.search_relevant(query=query, top_k=3)
            documents = rag_results.get("documents", [])
            
            if documents:
                combined_text = " ".join(documents)
                
                has_relevant = any(
                    kw in combined_text for kw in 
                    ["%", "分", "占比", "上限", "学时", "次数"]
                )
                
                if has_relevant:
                    status = "✓ 找到相关规则"
                    self.log_info(f"找到相关内容: {combined_text[:200]}...")
                else:
                    status = "⚠ 内容可能不完整"
                    self.record_issue(
                        issue_type="规则内容不完整",
                        query=rule_topic,
                        expected="包含具体数值或标准",
                        actual="未找到明确数值",
                        severity="中",
                        suggestion="检查文档切片是否保留了完整规则"
                    )
                
                results.append({
                    "topic": rule_topic,
                    "status": status,
                    "content_preview": combined_text[:200]
                })
            else:
                results.append({
                    "topic": rule_topic,
                    "status": "✗ 未找到相关内容"
                })
                self.record_issue(
                    issue_type="规则未找到",
                    query=rule_topic,
                    expected="有相关规则说明",
                    actual="无结果",
                    severity="高",
                    suggestion="检查文档是否已正确导入向量库"
                )
        
        duration_ms = (time.time() - start_time) * 1000
        found_count = sum(1 for r in results if "✓" in r.get("status", ""))
        coverage = found_count / len(key_rules) * 100
        
        self.log_info(f"\n综合测评规则验证完成: {found_count}/{len(key_rules)} 规则可检索 ({coverage:.1f}%)")
        self.record_result("综合测评规则验证", coverage >= 80, f"覆盖率: {coverage:.1f}%", duration_ms)
        
        return {
            "coverage": coverage,
            "found_count": found_count,
            "total_count": len(key_rules),
            "results": results
        }
    
    def compare_with_source_document(self) -> Dict[str, Any]:
        """与源文档进行对比验证 - 改进版：更智能的检索策略"""
        self.print_separator("源文档对比验证")
        start_time = time.time()
        
        if not self.docx_content:
            self.log_warn("未读取docx文档，跳过对比验证")
            return {"status": "skipped"}
        
        key_points = self._extract_key_points_from_docx()
        
        if not key_points:
            self.log_warn("未从文档中提取到关键点")
            return {"status": "no_key_points"}
        
        results = []
        matched_count = 0
        
        for point in key_points[:15]:
            keyword = point["keyword"]
            expected_content = point["content"]
            expected_value = point.get("value", "")
            comp_type = point.get("competition_type")
            level = point.get("level")
            award = point.get("award")
            
            search_queries = []
            
            if comp_type and level and award:
                search_queries.append(f"{comp_type}类 {level} {award} 加分 分数")
                search_queries.append(f"{comp_type}类竞赛 {level} {award}")
                search_queries.append(f"竞赛加分 {comp_type}类 {level}")
            elif award and str(award).startswith('CET'):
                cert_level = "四级" if "4" in str(award) else "六级"
                search_queries.append(f"英语{cert_level} 加分 分数")
                search_queries.append(f"CET{'4' if '4' in str(award) else '6'} 证书加分")
                search_queries.append(f"英语等级证书 {cert_level}")
            elif award and str(award).startswith('NCRE'):
                cert_level = "二级" if "2" in str(award) else "三级" if "3" in str(award) else "四级"
                search_queries.append(f"计算机{cert_level} 加分 分数")
                search_queries.append(f"NCRE 证书加分 {cert_level}")
                search_queries.append(f"计算机等级证书 {cert_level}")
            else:
                search_queries.append(keyword)
            
            metadata_filter = None
            if comp_type and level:
                metadata_filter = {
                    "competition_type": comp_type,
                    "level": level
                }
            elif award and str(award).startswith('CET'):
                metadata_filter = {"sub_category": "C3"}
            elif award and str(award).startswith('NCRE'):
                metadata_filter = {"sub_category": "C3"}
            
            all_documents = []
            all_metadatas = []
            all_distances = []
            
            for query in search_queries[:2]:
                rag_results = self.vector_db.search_relevant(
                    query=query, 
                    top_k=10,
                    metadata_filter=metadata_filter,
                    similarity_threshold=0.3
                )
                
                docs = rag_results.get("documents", [])
                metas = rag_results.get("metadatas", [])
                dists = rag_results.get("distances", [])
                
                all_documents.extend(docs)
                all_metadatas.extend(metas)
                all_distances.extend(dists)
            
            seen_docs = set()
            unique_docs = []
            unique_metas = []
            unique_dists = []
            
            for doc, meta, dist in zip(all_documents, all_metadatas, all_distances):
                doc_key = doc[:100]
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    unique_docs.append(doc)
                    unique_metas.append(meta)
                    unique_dists.append(dist)
            
            if unique_docs:
                best_similarity = 0.0
                best_doc = unique_docs[0]
                best_meta = unique_metas[0] if unique_metas else {}
                best_dist = unique_dists[0] if unique_dists else 1.0
                
                for doc, meta, dist in zip(unique_docs, unique_metas, unique_dists):
                    sim = self._calculate_text_similarity(expected_content, doc)
                    if sim > best_similarity:
                        best_similarity = sim
                        best_doc = doc
                        best_meta = meta
                        best_dist = dist
                
                score_match = False
                if expected_value:
                    actual_score = best_meta.get("score")
                    if actual_score and str(actual_score) == expected_value:
                        score_match = True
                    elif expected_value in best_doc:
                        score_match = True
                
                vector_sim = 1 / (1 + best_dist) if best_dist else 0.0
                
                combined_score = 0.6 * best_similarity + 0.3 * vector_sim + (0.1 if score_match else 0.0)
                
                if combined_score > 0.35 or score_match:
                    matched_count += 1
                    status = "✓ 匹配"
                    if score_match:
                        status = "✓ 分数匹配"
                else:
                    status = "⚠ 低相似度"
                    self.record_issue(
                        issue_type="内容相似度低",
                        query=keyword,
                        expected=expected_content[:100],
                        actual=best_doc[:100],
                        severity="中",
                        suggestion=f"综合分数{combined_score:.2f}，检查切片质量"
                    )
                
                results.append({
                    "keyword": keyword,
                    "text_similarity": best_similarity,
                    "vector_similarity": vector_sim,
                    "combined_score": combined_score,
                    "score_match": score_match,
                    "expected_score": expected_value,
                    "actual_score": best_meta.get("score"),
                    "status": status
                })
            else:
                results.append({
                    "keyword": keyword,
                    "status": "✗ 未检索到"
                })
                self.record_issue(
                    issue_type="检索无结果",
                    query=keyword,
                    expected=f"分数:{expected_value}",
                    actual="无结果",
                    severity="高",
                    suggestion="检查检索策略或向量库内容"
                )
        
        duration_ms = (time.time() - start_time) * 1000
        match_rate = matched_count / len(key_points[:15]) * 100 if key_points else 0
        
        self.log_info(f"\n源文档对比完成: 匹配率 {match_rate:.1f}%")
        self.record_result("源文档对比", match_rate >= 60, f"匹配率: {match_rate:.1f}%", duration_ms)
        
        return {
            "match_rate": match_rate,
            "matched_count": matched_count,
            "total_tested": len(key_points[:15]),
            "results": results
        }
    
    def _extract_key_points_from_docx(self) -> List[Dict[str, str]]:
        """从docx文档提取关键信息点 - 改进版：更精确的正则表达式"""
        key_points = []
        
        patterns = [
            {
                'pattern': r'([AB])类[^国省市]*?(国家级|省部级|省级|市级).*?(一等奖|二等奖|三等奖|特等奖).*?(\d+)\s*分',
                'keyword_template': '{comp_type}类{level}{award}加分',
                'extractor': lambda m: {
                    'competition_type': m.group(1),
                    'level': m.group(2),
                    'award': m.group(3),
                    'value': m.group(4)
                }
            },
            {
                'pattern': r'(英语|大学英语).*?(四级|六级|CET[46]).*?(\d+)\s*分',
                'keyword_template': '{subject}{cert}加分',
                'extractor': lambda m: {
                    'subject': m.group(1),
                    'cert': m.group(2),
                    'value': m.group(3),
                    'award': f'CET{4 if "四" in m.group(2) or "4" in m.group(2) else 6}'
                }
            },
            {
                'pattern': r'(计算机).*?(二级|三级|四级|NCRE[234]).*?(\d+)\s*分',
                'keyword_template': '{subject}{cert}加分',
                'extractor': lambda m: {
                    'subject': m.group(1),
                    'cert': m.group(2),
                    'value': m.group(3),
                    'award': f'NCRE{2 if "二" in m.group(2) or "2" in m.group(2) else 3 if "三" in m.group(2) else 4}'
                }
            },
        ]
        
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            keyword_template = pattern_info['keyword_template']
            extractor = pattern_info['extractor']
            
            for match in re.finditer(pattern, self.docx_content, re.IGNORECASE):
                try:
                    extracted = extractor(match)
                    
                    if 'competition_type' in extracted:
                        keyword = keyword_template.format(
                            comp_type=extracted['competition_type'],
                            level=extracted['level'],
                            award=extracted['award']
                        )
                    else:
                        keyword = keyword_template.format(
                            subject=extracted.get('subject', ''),
                            cert=extracted.get('cert', '')
                        )
                    
                    start = max(0, match.start() - 100)
                    end = min(len(self.docx_content), match.end() + 100)
                    
                    key_point = {
                        "keyword": keyword,
                        "content": self.docx_content[start:end],
                        "value": extracted['value'],
                        "competition_type": extracted.get('competition_type'),
                        "level": extracted.get('level'),
                        "award": extracted.get('award')
                    }
                    
                    if not any(kp['keyword'] == keyword for kp in key_points):
                        key_points.append(key_point)
                        
                except Exception as e:
                    self.log_warn(f"提取关键点失败: {e}")
                    continue
        
        return key_points
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度 - 改进版：更好的中文处理和关键词提取"""
        import re
        
        def preprocess_text(text: str) -> str:
            text = re.sub(r'【[^】]*】', '', text)
            text = re.sub(r'[\r\n\t]+', ' ', text)
            text = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        def extract_keywords(text: str) -> set:
            keywords = set()
            
            numbers = re.findall(r'\d+(?:\.\d+)?', text)
            keywords.update(numbers)
            
            key_patterns = [
                (r'A类|B类|C类', '竞赛类别'),
                (r'国家级|省级|省部级|市级|校级', '级别'),
                (r'一等奖|二等奖|三等奖|特等奖|优秀奖', '奖项'),
                (r'四级|六级|CET[46]|NCRE\d?', '证书类型'),
                (r'英语|计算机|数学|物理|化学', '学科'),
            ]
            
            for pattern, category in key_patterns:
                matches = re.findall(pattern, text)
                keywords.update(matches)
            
            important_terms = [
                '加分', '分数', '分值', '得分',
                '竞赛', '比赛', '证书', '考试',
                '通过', '合格', '优秀',
                '综合测评', '素质拓展',
            ]
            
            for term in important_terms:
                if term in text:
                    keywords.add(term)
            
            return keywords
        
        def extract_ngrams(text: str, n: int = 2) -> set:
            ngrams = set()
            for i in range(len(text) - n + 1):
                ngrams.add(text[i:i+n])
            return ngrams
        
        processed_text1 = preprocess_text(text1)
        processed_text2 = preprocess_text(text2)
        
        if not processed_text1 or not processed_text2:
            return 0.0
        
        keywords1 = extract_keywords(processed_text1)
        keywords2 = extract_keywords(processed_text2)
        
        keyword_sim = 0.0
        if keywords1 and keywords2:
            intersection = keywords1 & keywords2
            union = keywords1 | keywords2
            keyword_sim = len(intersection) / len(union) if union else 0.0
        
        bigrams1 = extract_ngrams(processed_text1, 2)
        bigrams2 = extract_ngrams(processed_text2, 2)
        
        char_sim = 0.0
        if bigrams1 and bigrams2:
            intersection = bigrams1 & bigrams2
            union = bigrams1 | bigrams2
            char_sim = len(intersection) / len(union) if union else 0.0
        
        number_bonus = 0.0
        nums1 = set(re.findall(r'\d+', processed_text1))
        nums2 = set(re.findall(r'\d+', processed_text2))
        if nums1 and nums2 and (nums1 & nums2):
            number_bonus = 0.1
        
        final_sim = 0.7 * keyword_sim + 0.3 * char_sim + number_bonus
        
        return min(final_sim, 1.0)
    
    def generate_optimization_suggestions(self) -> List[Dict[str, str]]:
        """生成优化建议"""
        self.print_separator("生成优化建议")
        
        suggestions = []
        
        for issue in self.accuracy_issues:
            suggestions.append({
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "query": issue.query,
                "suggestion": issue.suggestion
            })
        
        if self.performance_stats.get("rag_search"):
            avg_search_time = sum(self.performance_stats["rag_search"]) / len(self.performance_stats["rag_search"])
            if avg_search_time > 500:
                suggestions.append({
                    "issue_type": "检索性能",
                    "severity": "中",
                    "query": "N/A",
                    "suggestion": f"平均检索时间{avg_search_time:.0f}ms较高，建议优化向量索引或减少返回数量"
                })
        
        if len(self.accuracy_issues) > 5:
            suggestions.append({
                "issue_type": "整体准确性",
                "severity": "高",
                "query": "N/A",
                "suggestion": "发现多个准确性问题，建议：1) 检查文档切片大小（当前500字符）；2) 增加切片重叠（当前50字符）；3) 检查文档是否完整导入"
            })
        
        category_issues = [i for i in self.accuracy_issues if "类别" in i.issue_type]
        if len(category_issues) > 2:
            suggestions.append({
                "issue_type": "类别识别",
                "severity": "高",
                "query": "N/A",
                "suggestion": "竞赛类别识别问题较多，建议：1) 更新竞赛映射表；2) 增强类别关键词；3) 检查Excel数据完整性"
            })
        
        self.log_info(f"生成 {len(suggestions)} 条优化建议")
        for i, s in enumerate(suggestions, 1):
            self.log_info(f"  [{i}] [{s['severity']}] {s['issue_type']}: {s['suggestion']}")
        
        return suggestions
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        self.print_separator("测试报告")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        report = {
            "test_time": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": f"{passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "0%"
            },
            "accuracy_issues": [asdict(issue) for issue in self.accuracy_issues],
            "optimization_suggestions": self.generate_optimization_suggestions(),
            "performance_stats": {
                op: {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times) if times else 0,
                    "max_ms": max(times) if times else 0,
                    "min_ms": min(times) if times else 0
                }
                for op, times in self.performance_stats.items()
            },
            "test_results": [asdict(r) for r in self.test_results],
            "document_stats": {
                "docx_paragraphs": len(self.docx_paragraphs),
                "docx_chars": len(self.docx_content),
                "competition_records": len(self.competition_records)
            }
        }
        
        self.log_info(f"总测试数: {total_tests}")
        self.log_info(f"通过数: {passed_tests}")
        self.log_info(f"失败数: {failed_tests}")
        self.log_info(f"通过率: {report['summary']['pass_rate']}")
        self.log_info(f"发现问题数: {len(self.accuracy_issues)}")
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str = None):
        """保存测试报告"""
        if output_path is None:
            output_path = str(PROJECT_ROOT / "tests" / "rag_accuracy_report.json")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.log_success(f"报告已保存: {output_path}")
        except Exception as e:
            self.log_error(f"保存报告失败: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.print_separator("RAG检索准确性测试")
        self.log_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_info(f"docx文档: {DOCX_PATH}")
        self.log_info(f"xlsx文档: {XLSX_PATH}")
        
        self.read_docx_document(DOCX_PATH)
        self.read_xlsx_document(XLSX_PATH)
        
        if not self.init_rag_system():
            self.log_error("RAG系统初始化失败，无法继续测试")
            return self.generate_report()
        
        self.verify_competition_category()
        self.verify_score_rules()
        self.verify_comprehensive_evaluation_rules()
        self.compare_with_source_document()
        
        self.print_separator("示例检索演示")
        self.search_and_print("蓝桥杯国赛一等奖加多少分", top_k=3)
        self.search_with_category_awareness("英语四级证书可以加多少分")
        
        report = self.generate_report()
        self.save_report(report)
        
        return report


def main():
    """主函数"""
    tester = RAGAccuracyTester()
    report = tester.run_all_tests()
    
    print("\n" + "#" * 80)
    print("#  测试完成")
    print(f"#  通过率: {report['summary']['pass_rate']}")
    print(f"#  发现问题: {len(report['accuracy_issues'])} 个")
    print(f"#  优化建议: {len(report['optimization_suggestions'])} 条")
    print("#" * 80)
    
    return report


if __name__ == "__main__":
    main()
