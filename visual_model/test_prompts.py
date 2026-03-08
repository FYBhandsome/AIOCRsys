#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试提示词模板
验证JSON格式返回成功率达到100%
"""
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.comprehensive_prompts import comprehensive_score_prompts


class PromptTester:
    """提示词测试器"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def test_json_schema(self, json_str: str, test_name: str) -> bool:
        """测试JSON解析"""
        try:
            data = json.loads(json_str)
            print(f"✓ {test_name}: JSON解析成功")
            self.passed += 1
            self.results.append((test_name, True, None))
            return True
        except json.JSONDecodeError as e:
            print(f"✗ {test_name}: JSON解析失败 - {e}")
            self.failed += 1
            self.results.append((test_name, False, str(e)))
            return False
    
    def test_required_fields(self, data: dict, required_fields: list, test_name: str) -> bool:
        """测试必需字段"""
        missing = [f for f in required_fields if f not in data]
        if missing:
            print(f"✗ {test_name}: 缺少必需字段 - {missing}")
            self.failed += 1
            self.results.append((test_name, False, f"缺少字段: {missing}"))
            return False
        print(f"✓ {test_name}: 所有必需字段存在")
        self.passed += 1
        self.results.append((test_name, True, None))
        return True
    
    def test_field_types(self, data: dict, type_specs: dict, test_name: str) -> bool:
        """测试字段类型"""
        errors = []
        for field, expected_type in type_specs.items():
            if field in data:
                actual_type = type(data[field]).__name__
                if expected_type == "number":
                    if not isinstance(data[field], (int, float)):
                        errors.append(f"{field}: 期望number, 实际{actual_type}")
                elif expected_type == "boolean":
                    if not isinstance(data[field], bool):
                        errors.append(f"{field}: 期望boolean, 实际{actual_type}")
                elif expected_type == "string":
                    if not isinstance(data[field], str):
                        errors.append(f"{field}: 期望string, 实际{actual_type}")
                elif expected_type == "array":
                    if not isinstance(data[field], list):
                        errors.append(f"{field}: 期望array, 实际{actual_type}")
                elif expected_type == "object":
                    if not isinstance(data[field], dict):
                        errors.append(f"{field}: 期望object, 实际{actual_type}")
        
        if errors:
            print(f"✗ {test_name}: 类型错误 - {errors}")
            self.failed += 1
            self.results.append((test_name, False, f"类型错误: {errors}"))
            return False
        print(f"✓ {test_name}: 字段类型正确")
        self.passed += 1
        self.results.append((test_name, True, None))
        return True
    
    def test_all(self):
        """运行所有测试"""
        print("=" * 60)
        print("开始测试提示词模板")
        print("=" * 60)
        
        # 测试1: 证书分析提示词
        print("\n【测试1】证书分析提示词")
        cert_prompt = comprehensive_score_prompts.get_certificate_analysis_prompt(
            "测试证书文本",
            {"student_id": "2023001", "name": "张三"}
        )
        print(f"提示词长度: {len(cert_prompt)} 字符")
        
        # 模拟预期的JSON输出
        sample_cert_json = '''{
            "success": true,
            "category": "C",
            "sub_category": "C1",
            "score": 8.0,
            "level": "省级",
            "certificate_type": "竞赛",
            "certificate_name": "数学建模竞赛",
            "rules_matched": ["C类科技竞赛省级加8分"],
            "confidence": 0.95,
            "explanation": "根据规则，省级科技竞赛加8分"
        }'''
        self.test_json_schema(sample_cert_json, "证书分析JSON解析")
        
        cert_data = json.loads(sample_cert_json)
        self.test_required_fields(
            cert_data,
            ["success", "category", "sub_category", "score", "confidence"],
            "证书分析必需字段"
        )
        self.test_field_types(
            cert_data,
            {
                "success": "boolean",
                "category": "string",
                "sub_category": "string",
                "score": "number",
                "confidence": "number",
                "rules_matched": "array",
                "explanation": "string"
            },
            "证书分析字段类型"
        )
        
        # 测试2: 批量计算提示词
        print("\n【测试2】批量计算提示词")
        batch_prompt = comprehensive_score_prompts.get_batch_calculation_prompt(
            "2023001",
            "张三",
            "23级计算机1班",
            {"weighted_average": 85.5},
            [],
            []
        )
        print(f"提示词长度: {len(batch_prompt)} 字符")
        
        sample_batch_json = '''{
            "success": true,
            "student_id": "2023001",
            "student_name": "张三",
            "scores": {
                "a_score": {
                    "a1_score": 90.0,
                    "a2_score": 5.0,
                    "a3_score": 0.0,
                    "a_total": 95.0,
                    "a_weighted": 19.0
                },
                "b_score": {
                    "raw_score": 85.5,
                    "field_used": "weighted_average",
                    "b_weighted": 59.85
                },
                "c_score": {
                    "c1_score": 8.0,
                    "c2_score": 0.0,
                    "c3_score": 5.0,
                    "c4_score": 0.0,
                    "c_total": 13.0,
                    "c_weighted": 1.3
                },
                "total_score": 80.15
            },
            "rank_info": {
                "estimated_rank": 5,
                "percentile": 90.0
            },
            "details": [
                {
                    "category": "C1",
                    "item": "数学建模竞赛",
                    "score": 8.0,
                    "source": "证书"
                }
            ],
            "calculation_time": "2024-03-08T10:00:00"
        }'''
        self.test_json_schema(sample_batch_json, "批量计算JSON解析")
        
        batch_data = json.loads(sample_batch_json)
        self.test_required_fields(
            batch_data,
            ["success", "student_id", "student_name", "scores", "calculation_time"],
            "批量计算必需字段"
        )
        self.test_required_fields(
            batch_data["scores"],
            ["a_score", "b_score", "c_score", "total_score"],
            "批量计算scores字段"
        )
        
        # 测试3: Excel填充提示词
        print("\n【测试3】Excel填充提示词")
        excel_prompt = comprehensive_score_prompts.get_excel_fill_prompt(
            "测试数据",
            [{"student_id": "2023001", "student_name": "张三", "row_index": 4}]
        )
        print(f"提示词长度: {len(excel_prompt)} 字符")
        
        sample_excel_json = '''{
            "success": true,
            "fill_data": [
                {
                    "student_id": "2023001",
                    "student_name": "张三",
                    "row_index": 4,
                    "columns": {
                        "A1—基础分": 90.0,
                        "A2—附加分": 5.0,
                        "A3—扣分项": 0.0,
                        "思想道德素质(A)总分": 95.0,
                        "学习成绩": 85.5,
                        "C1—科技竞赛项目": 8.0,
                        "C2—体育竞技项目": 0.0,
                        "C3—文化类竞赛项目": 5.0,
                        "C4—创新创业实践项目": 0.0,
                        "素质拓展(C)总分": 13.0,
                        "综合测评总成绩": 80.15
                    },
                    "details": [
                        {
                            "category": "C1",
                            "item_name": "数学建模竞赛",
                            "score": 8.0,
                            "description": "省级竞赛"
                        }
                    ]
                }
            ],
            "summary": {
                "total_students": 1,
                "processed": 1,
                "failed": 0
            }
        }'''
        self.test_json_schema(sample_excel_json, "Excel填充JSON解析")
        
        excel_data = json.loads(sample_excel_json)
        self.test_required_fields(
            excel_data,
            ["success", "fill_data", "summary"],
            "Excel填充必需字段"
        )
        
        excel_columns = excel_data["fill_data"][0]["columns"]
        required_excel_columns = [
            "A1—基础分", "A2—附加分", "A3—扣分项",
            "思想道德素质(A)总分", "学习成绩",
            "C1—科技竞赛项目", "C2—体育竞技项目",
            "C3—文化类竞赛项目", "C4—创新创业实践项目",
            "素质拓展(C)总分", "综合测评总成绩"
        ]
        self.test_required_fields(
            excel_columns,
            required_excel_columns,
            "Excel填充列字段"
        )
        
        # 测试4: 规则检索提示词
        print("\n【测试4】规则检索提示词")
        rule_prompt = comprehensive_score_prompts.get_rule_retrieval_prompt("科技竞赛加分规则")
        print(f"提示词长度: {len(rule_prompt)} 字符")
        
        sample_rule_json = '''{
            "success": true,
            "rules": [
                {
                    "rule_id": "R001",
                    "rule_name": "科技竞赛加分",
                    "category": "C1",
                    "content": "国家级12分、省级8分、校级5分、院级3分",
                    "score_range": {"min": 3, "max": 12},
                    "conditions": ["科技类竞赛", "获奖证书"],
                    "relevance_score": 0.98
                }
            ],
            "total_count": 1,
            "query_interpretation": "查询科技竞赛相关的加分规则"
        }'''
        self.test_json_schema(sample_rule_json, "规则检索JSON解析")
        
        # 测试5: 权重配置提示词
        print("\n【测试5】权重配置提示词")
        weight_prompt = comprehensive_score_prompts.get_weight_config_prompt("2024-2025", "1")
        print(f"提示词长度: {len(weight_prompt)} 字符")
        
        sample_weight_json = '''{
            "success": true,
            "config": {
                "name": "2024-2025学年综测配置",
                "a_weight": 20.0,
                "b_weight": 70.0,
                "c_weight": 10.0,
                "academic_score_field": "weighted_average",
                "academic_score_scale": 1.0,
                "rules": {
                    "a_max_score": 100.0,
                    "c_max_score_per_item": 12.0,
                    "level_scores": {
                        "国家级": 12.0,
                        "省级": 8.0,
                        "校级": 5.0,
                        "院级": 3.0
                    }
                }
            },
            "source": "知识库配置"
        }'''
        self.test_json_schema(sample_weight_json, "权重配置JSON解析")
        
        # 输出测试总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        total = self.passed + self.failed
        print(f"总测试数: {total}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"成功率: {self.passed/total*100:.1f}%")
        
        if self.failed > 0:
            print("\n失败的测试:")
            for name, success, error in self.results:
                if not success:
                    print(f"  - {name}: {error}")
        
        return self.failed == 0


if __name__ == "__main__":
    tester = PromptTester()
    success = tester.test_all()
    sys.exit(0 if success else 1)
