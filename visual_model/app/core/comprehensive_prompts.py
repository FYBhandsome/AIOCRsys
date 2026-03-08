"""
综测计算专用Prompt模块
设计用于RAG检索并返回标准JSON格式的提示词

字段映射关系说明：
- 数据库字段 → JSON字段 → Excel列
- 详见各提示词中的字段映射表
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class ComprehensiveScorePrompts:
    """综测计算提示词管理类"""
    
    SYSTEM_PROMPT = """你是专业的综合测评计算助手，严格返回标准JSON。

【核心规则】
- A类（思想道德）：满分100，权重20%
- B类（学习成绩）：权重70%
- C类（素质拓展）：权重10%
  - C1科技/C2体育/C3文化/C4创业：国家级12分、省级8分、校级5分、院级3分

【JSON格式要求】
1. 纯JSON，无任何标记或文字
2. 数字不加引号，字符串用双引号
3. 从{开始，到}结束，无其他内容
4. 所有必需字段必须存在
5. 禁止使用```json或```代码块

【数据验证规则】
- 分数范围：A类0-100，C类各分项0-12
- 权重总和：A+B+C=100%
- confidence：0.0-1.0
- student_id：字符串格式"""

    FIELD_MAPPING = """
【字段映射对照表】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
数据库字段          JSON字段            Excel列
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
a1_score            a1_score            A1—基础分
a2_score            a2_score            A2—附加分
a3_score            a3_score            A3—扣分项
a_total_score       a_total             思想道德素质(A)总分
a_weighted_score    a_weighted          思想道德素质(A)总分%
b_raw_score         b_raw               学习成绩
b_weighted_score    b_weighted          学习成绩70%
c1_score            c1_score            C1—科技竞赛项目
c2_score            c2_score            C2—体育竞技项目
c3_score            c3_score            C3—文化类竞赛项目
c4_score            c4_score            C4—创新创业实践项目
c_total_score       c_total             素质拓展(C)总分
c_weighted_score    c_weighted          素质拓展(C)总分10%
total_score         total_score         综合测评总成绩8%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    CERTIFICATE_ANALYSIS_PROMPT = """分析证书信息，返回JSON。

证书文本：
{certificate_text}

学生信息：
{student_info}

【JSON Schema】
{{
    "success": "boolean, 必需",
    "category": "string, 必需, 可选值: A/C",
    "sub_category": "string, 必需, 可选值: A1/A2/A3/C1/C2/C3/C4",
    "score": "number, 必需, 加分值",
    "level": "string, 可选, 国家级/省级/校级/院级",
    "certificate_type": "string, 可选, 证书类型",
    "certificate_name": "string, 可选, 证书名称",
    "rules_matched": "array, 可选, 匹配的规则",
    "confidence": "number, 必需, 0.0-1.0",
    "explanation": "string, 可选, 加分说明"
}}

【数据验证】
- success必须为true或false
- category必须是"A"或"C"
- sub_category必须是A1/A2/A3/C1/C2/C3/C4之一
- score必须是数字
- confidence必须在0.0到1.0之间

【字段映射】
- category → Certificate.category
- sub_category → Certificate.sub_category
- score → Certificate.score
- level → Certificate.level
- certificate_name → Certificate.title""" + FIELD_MAPPING

    BATCH_CALCULATION_PROMPT = """计算学生综测成绩，返回JSON。

学生信息：
- 学号：{student_id}
- 姓名：{student_name}
- 班级：{class_name}

学业成绩：
{academic_info}

证书信息：
{certificate_info}

加减分明细：
{score_details}

【JSON Schema】
{{
    "success": "boolean, 必需",
    "student_id": "string, 必需",
    "student_name": "string, 必需",
    "scores": {{
        "a_score": {{
            "a1_score": "number, 必需, 0-100",
            "a2_score": "number, 必需, >=0",
            "a3_score": "number, 必需, <=0",
            "a_total": "number, 必需",
            "a_weighted": "number, 必需, =a_total*0.2"
        }},
        "b_score": {{
            "raw_score": "number, 必需",
            "field_used": "string, 必需",
            "b_weighted": "number, 必需, =raw_score*0.7"
        }},
        "c_score": {{
            "c1_score": "number, 必需, 0-12",
            "c2_score": "number, 必需, 0-12",
            "c3_score": "number, 必需, 0-12",
            "c4_score": "number, 必需, 0-12",
            "c_total": "number, 必需",
            "c_weighted": "number, 必需, =c_total*0.1"
        }},
        "total_score": "number, 必需, =a_weighted+b_weighted+c_weighted"
    }},
    "rank_info": {{
        "estimated_rank": "number, 可选",
        "percentile": "number, 可选"
    }},
    "details": [{{
        "category": "string, 必需",
        "item": "string, 必需",
        "score": "number, 必需",
        "source": "string, 必需"
    }}],
    "calculation_time": "string, 必需, ISO格式"
}}

【数据验证】
- a1_score：0-100
- a2_score：>=0
- a3_score：<=0
- c1-c4_score：每项0-12
- a_weighted = a_total * 0.2
- b_weighted = raw_score * 0.7
- c_weighted = c_total * 0.1
- total_score = a_weighted + b_weighted + c_weighted

【数据库字段映射】
- scores.a_score.a1_score → ComprehensiveScore.a1_score
- scores.a_score.a2_score → ComprehensiveScore.a2_score
- scores.a_score.a3_score → ComprehensiveScore.a3_score
- scores.a_score.a_total → ComprehensiveScore.a_total_score
- scores.a_score.a_weighted → ComprehensiveScore.a_weighted_score
- scores.b_score.raw_score → ComprehensiveScore.b_raw_score
- scores.b_score.b_weighted → ComprehensiveScore.b_weighted_score
- scores.c_score.c1_score → ComprehensiveScore.c1_score
- scores.c_score.c2_score → ComprehensiveScore.c2_score
- scores.c_score.c3_score → ComprehensiveScore.c3_score
- scores.c_score.c4_score → ComprehensiveScore.c4_score
- scores.c_score.c_total → ComprehensiveScore.c_total_score
- scores.c_score.c_weighted → ComprehensiveScore.c_weighted_score
- scores.total_score → ComprehensiveScore.total_score""" + FIELD_MAPPING

    RULE_RETRIEVAL_PROMPT = """检索综测规则，返回JSON。

查询：{query}

【JSON Schema】
{{
    "success": "boolean, 必需",
    "rules": [{{
        "rule_id": "string, 必需",
        "rule_name": "string, 必需",
        "category": "string, 必需",
        "content": "string, 必需",
        "score_range": {{
            "min": "number, 必需",
            "max": "number, 必需"
        }},
        "conditions": "array, 必需",
        "relevance_score": "number, 必需, 0.0-1.0"
    }}],
    "total_count": "number, 必需",
    "query_interpretation": "string, 必需"
}}"""

    WEIGHT_CONFIG_PROMPT = """返回综测权重配置JSON。

学年：{academic_year}
学期：{semester}

【JSON Schema】
{{
    "success": "boolean, 必需",
    "config": {{
        "name": "string, 必需",
        "a_weight": "number, 必需, 0-100",
        "b_weight": "number, 必需, 0-100",
        "c_weight": "number, 必需, 0-100",
        "academic_score_field": "string, 必需",
        "academic_score_scale": "number, 必需",
        "rules": {{
            "a_max_score": "number, 必需",
            "c_max_score_per_item": "number, 必需",
            "level_scores": {{
                "国家级": "number, 必需",
                "省级": "number, 必需",
                "校级": "number, 必需",
                "院级": "number, 必需"
            }}
        }}
    }},
    "source": "string, 必需"
}}

【数据验证】
- a_weight + b_weight + c_weight = 100
- 每项权重 0-100

【数据库字段映射】
- config.a_weight → ComprehensiveScoreConfig.a_weight
- config.b_weight → ComprehensiveScoreConfig.b_weight
- config.c_weight → ComprehensiveScoreConfig.c_weight
- config.academic_score_field → ComprehensiveScoreConfig.academic_score_field
- config.academic_score_scale → ComprehensiveScoreConfig.academic_score_scale"""

    EXCEL_FILL_PROMPT = """生成Excel填充数据JSON。

原始数据：
{raw_data}

学生列表：
{student_list}

【JSON Schema】
{{
    "success": "boolean, 必需",
    "fill_data": [{{
        "student_id": "string, 必需",
        "student_name": "string, 必需",
        "row_index": "number, 必需",
        "columns": {{
            "A1—基础分": "number, 必需, 0-100",
            "A2—附加分": "number, 必需, >=0",
            "A3—扣分项": "number, 必需, <=0",
            "思想道德素质(A)总分": "number, 必需",
            "学习成绩": "number, 必需",
            "C1—科技竞赛项目": "number, 必需, 0-12",
            "C2—体育竞技项目": "number, 必需, 0-12",
            "C3—文化类竞赛项目": "number, 必需, 0-12",
            "C4—创新创业实践项目": "number, 必需, 0-12",
            "素质拓展(C)总分": "number, 必需",
            "综合测评总成绩": "number, 必需"
        }},
        "details": [{{
            "category": "string, 必需",
            "item_name": "string, 必需",
            "score": "number, 必需",
            "description": "string, 可选"
        }}]
    }}],
    "summary": {{
        "total_students": "number, 必需",
        "processed": "number, 必需",
        "failed": "number, 必需"
    }}
}}

【数据验证】
- A1—基础分：0-100
- A2—附加分：>=0
- A3—扣分项：<=0
- C1-C4：每项0-12
- 所有columns字段必须存在

【字段映射】
- fill_data[].columns["A1—基础分"] → Excel列A1—基础分
- fill_data[].columns["A2—附加分"] → Excel列A2—附加分
- fill_data[].columns["A3—扣分项"] → Excel列A3—扣分项
- fill_data[].columns["思想道德素质(A)总分"] → Excel列思想道德素质(A)总分
- fill_data[].columns["学习成绩"] → Excel列学习成绩
- fill_data[].columns["C1—科技竞赛项目"] → Excel列C1—科技竞赛项目
- fill_data[].columns["C2—体育竞技项目"] → Excel列C2—体育竞技项目
- fill_data[].columns["C3—文化类竞赛项目"] → Excel列C3—文化类竞赛项目
- fill_data[].columns["C4—创新创业实践项目"] → Excel列C4—创新创业实践项目
- fill_data[].columns["素质拓展(C)总分"] → Excel列素质拓展(C)总分
- fill_data[].columns["综合测评总成绩"] → Excel列综合测评总成绩8%""" + FIELD_MAPPING

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
