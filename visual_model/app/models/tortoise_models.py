#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tortoise ORM 数据模型
"""

from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional


class User(Model):
    """用户模型"""
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=255, unique=True, null=True, description="邮箱")
    password = fields.CharField(max_length=255, description="密码（加密存储）")
    role = fields.CharField(max_length=20, default="student", description="角色：student, teacher, admin")
    
    # 学生相关信息
    student_id = fields.CharField(max_length=50, null=True, unique=True, description="学号")
    real_name = fields.CharField(max_length=100, null=True, description="真实姓名")
    class_id = fields.CharField(max_length=50, null=True, description="班级ID")
    
    # 账户状态
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_email_verified = fields.BooleanField(default=False, description="邮箱是否验证")
    
    # 密码重置
    reset_token = fields.CharField(max_length=255, null=True, description="密码重置令牌")
    reset_token_expires = fields.DatetimeField(null=True, description="重置令牌过期时间")
    
    # 登录信息
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # 其他信息可以存储在 JSON 字段中
    extra_info = fields.JSONField(null=True, description="其他信息")
    
    class Meta:
        table = "users"
        table_description = "用户信息表"
    
    def __str__(self):
        return f"User({self.username}, {self.role})"


class Student(Model):
    """学生模型"""
    id = fields.CharField(pk=True, max_length=50, description="学号")
    name = fields.CharField(max_length=100, description="姓名")
    college = fields.CharField(max_length=100, description="学院")
    major = fields.CharField(max_length=100, description="专业")
    class_name = fields.CharField(max_length=50, description="班级")
    grade = fields.CharField(max_length=20, description="年级")
    
    # 综测相关
    total_score = fields.FloatField(default=0.0, description="综测总成绩")
    
    # 宿舍相关
    dormitory_number = fields.CharField(max_length=50, null=True, description="宿舍编号")
    dormitory_score = fields.FloatField(null=True, description="宿舍成绩")
    
    # 体测成绩
    physical_test_score = fields.FloatField(null=True, description="体测成绩")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # 关联关系
    activities: fields.ReverseRelation["Activity"]
    score_records: fields.ReverseRelation["ScoreRecord"]
    comprehensive_scores: fields.ReverseRelation["ComprehensiveScore"]
    
    class Meta:
        table = "students"
        table_description = "学生信息表"
    
    def __str__(self):
        return f"{self.name}({self.id})"


class Activity(Model):
    """活动模型"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=200)
    type = fields.CharField(max_length=50)
    details = fields.JSONField()
    score = fields.FloatField()
    status = fields.CharField(max_length=20, default="pending")  # pending, approved, rejected
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # 关联关系
    student: fields.ForeignKeyRelation[Student] = fields.ForeignKeyField(
        "models.Student", related_name="activities"
    )
    
    class Meta:
        table = "activities"
        table_description = "学生活动表"
    
    def __str__(self):
        return f"{self.name}({self.student_id})"


class ScoreRecord(Model):
    """分数记录模型"""
    id = fields.IntField(pk=True)
    total_score = fields.FloatField()
    details = fields.JSONField()
    created_at = fields.DatetimeField(auto_now_add=True)
    
    # 关联关系
    student: fields.ForeignKeyRelation[Student] = fields.ForeignKeyField(
        "models.Student", related_name="score_records"
    )
    
    class Meta:
        table = "score_records"
        table_description = "分数记录表"
    
    def __str__(self):
        return f"ScoreRecord({self.student_id}, {self.total_score})"


class ComprehensiveScore(Model):
    """综测类别总成绩模型"""
    id = fields.IntField(pk=True)
    
    # A类材料成绩
    a_total_score = fields.FloatField(default=0.0, description="A类材料总成绩")
    a1_score = fields.FloatField(default=0.0, description="A1类成绩")
    a2_score = fields.FloatField(default=0.0, description="A2类成绩")
    a3_score = fields.FloatField(default=0.0, description="A3类成绩")
    
    # B类材料成绩
    b_total_score = fields.FloatField(default=0.0, description="B类材料总成绩（学习成绩）")
    
    # C类材料成绩
    c_total_score = fields.FloatField(default=0.0, description="C类材料总成绩")
    c1_score = fields.FloatField(default=0.0, description="C1类成绩")
    c2_score = fields.FloatField(default=0.0, description="C2类成绩")
    c3_score = fields.FloatField(default=0.0, description="C3类成绩")
    c4_score = fields.FloatField(default=0.0, description="C4类成绩")
    
    # 综测总成绩
    total_score = fields.FloatField(default=0.0, description="综测总成绩")
    
    # 学期信息
    semester = fields.CharField(max_length=20, description="学期，如：2024-1")
    academic_year = fields.CharField(max_length=20, description="学年，如：2024-2025")
    
    # 备注和详细信息
    remarks = fields.TextField(null=True, description="备注")
    details = fields.JSONField(null=True, description="详细分数信息")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # 关联关系
    student: fields.ForeignKeyRelation[Student] = fields.ForeignKeyField(
        "models.Student", related_name="comprehensive_scores"
    )
    
    class Meta:
        table = "comprehensive_scores"
        table_description = "综测类别总成绩表"
        unique_together = (("student_id", "semester", "academic_year"),)
    
    def __str__(self):
        return f"ComprehensiveScore({self.student_id}, {self.semester}, {self.total_score})"




class File(Model):
    """文件模型"""
    id = fields.CharField(pk=True, max_length=50)
    filename = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=500)
    file_size = fields.IntField()
    file_type = fields.CharField(max_length=50)
    student_id = fields.CharField(max_length=50, null=True, description="关联学生ID")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "files"
        table_description = "文件表"
    
    def __str__(self):
        return f"File({self.filename})"