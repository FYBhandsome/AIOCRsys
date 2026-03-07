#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测成绩相关模型
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional


class ComprehensiveScoreConfig(Model):
    """综测成绩配置模型"""
    id = fields.IntField(pk=True)
    
    name = fields.CharField(max_length=100, description="配置名称")
    description = fields.TextField(null=True, description="配置描述")
    
    a_weight = fields.FloatField(default=20.0, description="A类材料权重（%）")
    b_weight = fields.FloatField(default=70.0, description="B类材料（学习成绩）权重（%）")
    c_weight = fields.FloatField(default=10.0, description="C类材料权重（%）")
    
    academic_score_field = fields.CharField(
        max_length=50,
        default="weighted_average",
        description="学业成绩使用的字段"
    )
    
    academic_score_scale = fields.FloatField(
        default=1.0,
        description="学业成绩缩放系数（GPA转百分制时用25）"
    )
    
    is_active = fields.BooleanField(default=True, description="是否启用此配置")
    is_default = fields.BooleanField(default=False, description="是否为默认配置")
    
    applicable_grade = fields.CharField(max_length=20, null=True, description="适用年级")
    applicable_semester = fields.CharField(max_length=20, null=True, description="适用学期")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "comprehensive_score_configs"
        table_description = "综测成绩配置表"
    
    def __str__(self):
        return f"ComprehensiveScoreConfig({self.name})"
    
    def validate_weights(self) -> bool:
        """验证权重总和是否为100"""
        total = self.a_weight + self.b_weight + self.c_weight
        return abs(total - 100.0) < 0.01


class ComprehensiveScore(Model):
    """综测类别总成绩模型"""
    id = fields.IntField(pk=True)
    
    student_id = fields.CharField(max_length=50, description="学号")
    student_name = fields.CharField(max_length=100, null=True, description="姓名")
    class_name = fields.CharField(max_length=50, null=True, description="班级")
    major = fields.CharField(max_length=100, null=True, description="专业")
    
    a_total_score = fields.FloatField(default=0.0, description="A类材料总成绩")
    a1_score = fields.FloatField(default=0.0, description="A1类成绩")
    a2_score = fields.FloatField(default=0.0, description="A2类成绩")
    a3_score = fields.FloatField(default=0.0, description="A3类成绩")
    a_weighted_score = fields.FloatField(default=0.0, description="A类加权成绩(20%)")
    
    b_raw_score = fields.FloatField(default=0.0, description="B类原始成绩")
    b_weighted_score = fields.FloatField(default=0.0, description="B类加权成绩(70%)")
    
    c_total_score = fields.FloatField(default=0.0, description="C类材料总成绩")
    c1_score = fields.FloatField(default=0.0, description="C1类成绩-科技竞赛")
    c2_score = fields.FloatField(default=0.0, description="C2类成绩-体育竞技")
    c3_score = fields.FloatField(default=0.0, description="C3类成绩-文化竞赛")
    c4_score = fields.FloatField(default=0.0, description="C4类成绩-创新创业")
    c_weighted_score = fields.FloatField(default=0.0, description="C类加权成绩(10%)")
    
    total_score = fields.FloatField(default=0.0, description="综测总成绩")
    ranking = fields.IntField(null=True, description="班级排名")
    
    semester = fields.CharField(max_length=20, description="学期，如：1")
    academic_year = fields.CharField(max_length=20, description="学年，如：2024-2025")
    
    config_id = fields.IntField(null=True, description="使用的配置ID")
    
    source_file = fields.CharField(max_length=255, null=True, description="来源文件名")
    source_type = fields.CharField(max_length=20, default="comprehensive_table", description="来源类型")
    
    remarks = fields.TextField(null=True, description="备注")
    details = fields.JSONField(null=True, description="详细分数信息")
    status = fields.CharField(max_length=20, default="active", description="状态")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "comprehensive_scores"
        table_description = "综测类别总成绩表"
        unique_together = (("student_id", "semester", "academic_year"),)
        indexes = [
            ("student_id",),
            ("ranking",),
            ("semester", "academic_year"),
        ]
    
    def __str__(self):
        return f"ComprehensiveScore({self.student_id}, {self.semester}, {self.total_score})"


class ScoreDetail(Model):
    """综测加减分明细模型"""
    id = fields.IntField(pk=True)
    
    student_id = fields.CharField(max_length=50, description="学生ID")
    semester = fields.CharField(max_length=20, description="学期")
    academic_year = fields.CharField(max_length=20, description="学年")
    
    category_type = fields.CharField(max_length=10, description="类别: A1, A2, A3, C1, C2, C3, C4")
    item_name = fields.CharField(max_length=255, description="项目名称")
    score = fields.FloatField(default=0.0, description="分数（正数为加分，负数为扣分）")
    
    description = fields.TextField(null=True, description="详细说明")
    source = fields.CharField(max_length=50, null=True, description="来源：manual(手动录入), import(导入), ocr(OCR识别)")
    
    certificate_id = fields.IntField(null=True, description="关联证书ID")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "score_details"
        table_description = "综测加减分明细表"
        indexes = [("student_id",), ("category_type",), ("semester", "academic_year")]
    
    def __str__(self):
        return f"ScoreDetail({self.student_id}, {self.category_type}, {self.score})"


class ComprehensiveScoreHistory(Model):
    """综测成绩历史记录模型 - 用于版本控制"""
    id = fields.IntField(pk=True)
    
    comprehensive_score_id = fields.IntField(description="关联的综测成绩ID")
    student_id = fields.CharField(max_length=50, description="学号")
    
    version = fields.IntField(default=1, description="版本号")
    
    a_total_score = fields.FloatField(default=0.0, description="A类总分")
    a1_score = fields.FloatField(default=0.0, description="A1类成绩")
    a2_score = fields.FloatField(default=0.0, description="A2类成绩")
    a3_score = fields.FloatField(default=0.0, description="A3类成绩")
    
    b_total_score = fields.FloatField(default=0.0, description="B类总分")
    
    c_total_score = fields.FloatField(default=0.0, description="C类总分")
    c1_score = fields.FloatField(default=0.0, description="C1类成绩")
    c2_score = fields.FloatField(default=0.0, description="C2类成绩")
    c3_score = fields.FloatField(default=0.0, description="C3类成绩")
    c4_score = fields.FloatField(default=0.0, description="C4类成绩")
    
    total_score = fields.FloatField(default=0.0, description="综测总成绩")
    
    semester = fields.CharField(max_length=20, description="学期")
    academic_year = fields.CharField(max_length=20, description="学年")
    
    config_id = fields.IntField(null=True, description="使用的配置ID")
    raw_data = fields.JSONField(null=True, description="原始数据快照")
    
    change_type = fields.CharField(max_length=20, default="create", description="变更类型: create, update, calculate")
    change_reason = fields.TextField(null=True, description="变更原因")
    changed_by = fields.CharField(max_length=50, null=True, description="操作人")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "comprehensive_score_history"
        table_description = "综测成绩历史记录表"
        indexes = [("student_id",), ("comprehensive_score_id",), ("semester", "academic_year")]
    
    def __str__(self):
        return f"ComprehensiveScoreHistory({self.student_id}, v{self.version})"
