#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学业成绩相关模型
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.student import Student


class AcademicScore(Model):
    """学业成绩模型（课程成绩）"""
    id = fields.IntField(pk=True)
    
    student_name = fields.CharField(max_length=100, description="姓名")
    college = fields.CharField(max_length=100, null=True, description="学院")
    grade = fields.CharField(max_length=20, null=True, description="年级")
    major = fields.CharField(max_length=100, null=True, description="专业")
    class_name = fields.CharField(max_length=50, null=True, description="班级")
    
    total_score = fields.FloatField(default=0.0, description="总分")
    total_required_credits = fields.FloatField(default=0.0, description="总应获得学分")
    course_count = fields.IntField(default=0, description="门数")
    total_credits = fields.FloatField(default=0.0, description="总学分")
    earned_credits = fields.FloatField(default=0.0, description="获得学分")
    failed_credits = fields.FloatField(default=0.0, description="不及格学分")
    
    pass_rate = fields.FloatField(default=0.0, description="通过率（%）")
    arithmetic_average = fields.FloatField(default=0.0, description="算术平均分")
    arithmetic_average_rank = fields.IntField(null=True, description="算术平均分排名")
    
    weighted_average = fields.FloatField(default=0.0, description="学分加权平均分")
    weighted_average_rank = fields.IntField(null=True, description="学分加权平均分排名")
    
    average_gpa = fields.FloatField(default=0.0, description="平均绩点")
    average_gpa_rank = fields.IntField(null=True, description="平均绩点排名")
    average_credit_gpa = fields.FloatField(default=0.0, description="平均学分绩点")
    average_credit_gpa_rank = fields.IntField(null=True, description="平均学分绩点排名")
    credit_gpa_sum = fields.FloatField(default=0.0, description="学分绩点和")
    credit_gpa_sum_rank = fields.IntField(null=True, description="学分绩点和排名")
    
    failed_course_count = fields.IntField(default=0, description="不及格门次")
    
    semester = fields.CharField(max_length=20, null=True, description="学期，如：2024-1")
    academic_year = fields.CharField(max_length=20, null=True, description="学年，如：2024-2025")
    
    source_file = fields.CharField(max_length=255, null=True, description="来源文件名")
    source_type = fields.CharField(max_length=20, default="score_sheet", description="来源类型")
    
    remarks = fields.TextField(null=True, description="备注")
    details = fields.JSONField(null=True, description="详细课程成绩信息")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    student: fields.ForeignKeyRelation["Student"] = fields.ForeignKeyField(
        "models.Student", related_name="academic_scores", null=True
    )
    
    class Meta:
        table = "academic_scores"
        table_description = "学业成绩表"
        unique_together = (("student_id", "semester", "academic_year"),)
    
    def __str__(self):
        return f"AcademicScore({self.student_id}, {self.student_name}, {self.semester})"


class AcademicScoreHistory(Model):
    """学业成绩历史记录模型 - 用于版本控制"""
    id = fields.IntField(pk=True)
    
    academic_score_id = fields.IntField(description="关联的学业成绩ID")
    student_id = fields.CharField(max_length=50, description="学号")
    
    version = fields.IntField(default=1, description="版本号")
    
    total_score = fields.FloatField(default=0.0, description="总分")
    course_count = fields.IntField(default=0, description="门数")
    total_credits = fields.FloatField(default=0.0, description="总学分")
    earned_credits = fields.FloatField(default=0.0, description="获得学分")
    arithmetic_average = fields.FloatField(default=0.0, description="算术平均分")
    weighted_average = fields.FloatField(default=0.0, description="学分加权平均分")
    average_gpa = fields.FloatField(default=0.0, description="平均绩点")
    average_credit_gpa = fields.FloatField(default=0.0, description="平均学分绩点")
    
    failed_course_count = fields.IntField(default=0, description="不及格门次")
    
    semester = fields.CharField(max_length=20, description="学期")
    academic_year = fields.CharField(max_length=20, description="学年")
    
    source_file = fields.CharField(max_length=255, null=True, description="来源文件名")
    raw_data = fields.JSONField(null=True, description="原始数据快照")
    
    change_type = fields.CharField(max_length=20, default="create", description="变更类型: create, update, import")
    change_reason = fields.TextField(null=True, description="变更原因")
    changed_by = fields.CharField(max_length=50, null=True, description="操作人")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "academic_score_history"
        table_description = "学业成绩历史记录表"
        indexes = [("student_id",), ("academic_score_id",), ("semester", "academic_year")]
    
    def __str__(self):
        return f"AcademicScoreHistory({self.student_id}, v{self.version})"
