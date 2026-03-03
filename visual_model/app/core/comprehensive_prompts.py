"""
综测计算专用Prompt模块
设计用于RAG检索并返回标准JSON格式的提示词
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class ComprehensiveScorePrompts:
    """综测计算提示词管理类"""
    
    SYSTEM_PROMPT = """你是一个专业的综合测评计算助手，负责根据学生提交的材料计算综测成绩。
你需要严格按照综测规则进行计算，并返回标准JSON格式的结果。

重要规则：
1. A类材料（思想道德素质）：满分100分，占比20%
   - A1基础分：满分100分
   - A2附加分：根据获奖、荣誉等加分
   - A3扣罚分：根据违纪等情况扣分

2. B类材料（学习成绩）：占比70%
   - 使用学分加权平均分或GPA转换

3. C类材料（素质拓展）：占比10%
   - C1科技类竞赛：国家级12分、省级8分、校级5分、院级3分
   - C2体育竞技：参照C1标准
   - C3文化类竞赛：参照C1标准
   - C4创新创业：参照C1标准

========================================
【重要格式要求 - 必须严格遵守】
========================================
1. 必须返回纯JSON格式，不要使用```json或```代码块标记
2. 不要在JSON前后添加任何解释性文字、说明或注释
3. 不要添加"以下是结果"、"返回数据如下"等引导语
4. JSON必须完整且可解析，确保所有引号、括号正确闭合
5. 数字类型不要加引号，字符串类型必须加引号
6. 直接输出JSON，从{开始，到}结束

正确示例：
{"success": true, "score": 85.5, "name": "张三"}

错误示例（禁止）：
```json
{"success": true, "score": 85.5}
```
或者：
以下是计算结果：{"success": true, "score": 85.5}
========================================"""
    
    CERTIFICATE_ANALYSIS_PROMPT = """请分析以下证书信息，并返回JSON格式的加分结果。

证书OCR识别文本：
{certificate_text}

学生信息：
{student_info}

========================================
【重要格式要求】
1. 必须返回纯JSON格式，不要使用```json或```代码块标记
2. 不要添加任何解释性文字，直接输出JSON
3. JSON必须完整且可解析
========================================

请严格按照以下JSON格式返回结果：
{{
    "success": true,
    "category": "A或C",
    "sub_category": "A1/A2/A3/C1/C2/C3/C4",
    "score": 加分值(数字),
    "level": "国家级/省级/校级/院级",
    "certificate_type": "证书类型",
    "certificate_name": "证书名称",
    "rules_matched": ["匹配的规则条文"],
    "confidence": 置信度(0.0-1.0),
    "explanation": "加分说明"
}}"""
    
    BATCH_CALCULATION_PROMPT = """请根据以下学生信息计算综测成绩，返回标准JSON格式。

学生基本信息：
- 学号：{student_id}
- 姓名：{student_name}
- 班级：{class_name}

学业成绩信息：
{academic_info}

证书/获奖信息：
{certificate_info}

加减分明细：
{score_details}

========================================
【重要格式要求】
1. 必须返回纯JSON格式，不要使用```json或```代码块标记
2. 不要添加任何解释性文字，直接输出JSON
3. JSON必须完整且可解析
========================================

请严格按照以下JSON格式返回结果：
{{
    "success": true,
    "student_id": "学号",
    "student_name": "姓名",
    "scores": {{
        "a_score": {{
            "a1_score": A1基础分,
            "a2_score": A2附加分,
            "a3_score": A3扣罚分(负数),
            "a_total": A类总分,
            "a_weighted": A类加权分(总分*20%)
        }},
        "b_score": {{
            "raw_score": 学业成绩原始分,
            "field_used": "使用的字段名",
            "b_weighted": B类加权分(学业成绩*70%)
        }},
        "c_score": {{
            "c1_score": C1科技类分数,
            "c2_score": C2体育类分数,
            "c3_score": C3文化类分数,
            "c4_score": C4创新创业分数,
            "c_total": C类总分,
            "c_weighted": C类加权分(总分*10%)
        }},
        "total_score": 综测总成绩
    }},
    "rank_info": {{
        "estimated_rank": 预估排名,
        "percentile": 百分位
    }},
    "details": [
        {{
            "category": "类别",
            "item": "项目名称",
            "score": 分数,
            "source": "来源说明"
        }}
    ],
    "calculation_time": "计算时间"
}}"""
    
    RULE_RETRIEVAL_PROMPT = """请从知识库中检索与以下问题相关的综测规则，并返回JSON格式结果。

查询问题：{query}

========================================
【重要格式要求】
1. 必须返回纯JSON格式，不要使用```json或```代码块标记
2. 不要添加任何解释性文字，直接输出JSON
3. JSON必须完整且可解析
========================================

请严格按照以下JSON格式返回结果：
{{
    "success": true,
    "rules": [
        {{
            "rule_id": "规则ID",
            "rule_name": "规则名称",
            "category": "适用类别",
            "content": "规则内容",
            "score_range": {{
                "min": 最低分,
                "max": 最高分
            }},
            "conditions": ["适用条件"],
            "relevance_score": 相关度(0.0-1.0)
        }}
    ],
    "total_count": 规则总数,
    "query_interpretation": "查询意图解释"
}}"""
    
    WEIGHT_CONFIG_PROMPT = """请根据知识库中的配置，返回综测成绩计算的权重配置。

学年：{academic_year}
学期：{semester}

========================================
【重要格式要求】
1. 必须返回纯JSON格式，不要使用```json或```代码块标记
2. 不要添加任何解释性文字，直接输出JSON
3. JSON必须完整且可解析
========================================

请严格按照以下JSON格式返回结果：
{{
    "success": true,
    "config": {{
        "name": "配置名称",
        "a_weight": A类权重百分比,
        "b_weight": B类权重百分比,
        "c_weight": C类权重百分比,
        "academic_score_field": "学业成绩使用的字段",
        "academic_score_scale": 学业成绩缩放系数,
        "rules": {{
            "a_max_score": A类最高分,
            "c_max_score_per_item": C类单项最高分,
            "level_scores": {{
                "国家级": 分数,
                "省级": 分数,
                "校级": 分数,
                "院级": 分数
            }}
        }}
    }},
    "source": "配置来源说明"
}}"""
    
    EXCEL_FILL_PROMPT = """请根据以下学生数据，生成用于填充Excel表格的JSON数据。

原始数据（OCR识别或成绩单）：
{raw_data}

学生列表：
{student_list}

========================================
【重要格式要求】
1. 必须返回纯JSON格式，不要使用```json或```代码块标记
2. 不要添加任何解释性文字，直接输出JSON
3. JSON必须完整且可解析
========================================

请严格按照以下JSON格式返回，确保数据可以按学号匹配填充到Excel：
{{
    "success": true,
    "fill_data": [
        {{
            "student_id": "学号",
            "student_name": "姓名",
            "row_index": 行号,
            "columns": {{
                "A1—基础分": 分数,
                "A2—附加分": 分数,
                "A3—扣罚分": 分数,
                "思想道德素质(A)总分": 分数,
                "学习成绩": 分数,
                "C1—科技类竞赛项目": 分数,
                "C2—体育竞技项目": 分数,
                "C3—文化类竞赛项目": 分数,
                "C4—创新创业实践项目": 分数,
                "素质拓展（C）总分": 分数,
                "综合测评总成绩": 分数
            }},
            "details": [
                {{
                    "category": "类别",
                    "item_name": "项目名称",
                    "score": 分数,
                    "description": "详细说明"
                }}
            ]
        }}
    ],
    "summary": {{
        "total_students": 学生总数,
        "processed": 处理成功数,
        "failed": 处理失败数
    }}
}}"""
    
    @classmethod
    def get_certificate_analysis_prompt(cls, certificate_text: str, student_info: Dict = None) -> str:
        """获取证书分析提示词"""
        return cls.CERTIFICATE_ANALYSIS_PROMPT.format(
            certificate_text=certificate_text,
            student_info=str(student_info) if student_info else "无"
        )
    
    @classmethod
    def get_batch_calculation_prompt(cls, student_id: str, student_name: str, 
                                     class_name: str, academic_info: Dict,
                                     certificate_info: List, score_details: List) -> str:
        """获取批量计算提示词"""
        return cls.BATCH_CALCULATION_PROMPT.format(
            student_id=student_id,
            student_name=student_name,
            class_name=class_name,
            academic_info=str(academic_info),
            certificate_info=str(certificate_info),
            score_details=str(score_details)
        )
    
    @classmethod
    def get_rule_retrieval_prompt(cls, query: str) -> str:
        """获取规则检索提示词"""
        return cls.RULE_RETRIEVAL_PROMPT.format(query=query)
    
    @classmethod
    def get_weight_config_prompt(cls, academic_year: str, semester: str) -> str:
        """获取权重配置提示词"""
        return cls.WEIGHT_CONFIG_PROMPT.format(
            academic_year=academic_year,
            semester=semester
        )
    
    @classmethod
    def get_excel_fill_prompt(cls, raw_data: str, student_list: List) -> str:
        """获取Excel填充提示词"""
        return cls.EXCEL_FILL_PROMPT.format(
            raw_data=raw_data,
            student_list=str(student_list)
        )


comprehensive_score_prompts = ComprehensiveScorePrompts()
