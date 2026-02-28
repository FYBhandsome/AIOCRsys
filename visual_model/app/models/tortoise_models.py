#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tortoise ORM 数据模型
"""

from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional


'''
Tortoise ORM 数据模型
    用户模型
    班级模型
    学生模型
    学业成绩模型（AcademicScore）
    综测配置模型（ComprehensiveScoreConfig）
    综测类别总成绩模型
    综测加减分明细模型
    文件模型
    证书模型
'''

class Class(Model):
    """班级模型"""
    id = fields.CharField(pk=True, max_length=50, description="班级编号，如230521")
    name = fields.CharField(max_length=100, description="班级名称")
    grade = fields.CharField(max_length=20, description="年级")
    major = fields.CharField(max_length=100, description="专业")
    college = fields.CharField(max_length=100, description="学院")
    
    student_count = fields.IntField(default=0, description="学生人数")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "classes"
        table_description = "班级信息表"
    
    def __str__(self):
        return f"Class({self.id}, {self.name})"


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
    
    # 邮箱验证码（用于密码重置等）
    verification_code = fields.CharField(max_length=10, null=True, description="验证码")
    code_expires_at = fields.DatetimeField(null=True, description="验证码过期时间")
    
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
    academic_scores: fields.ReverseRelation["AcademicScore"]
    comprehensive_scores: fields.ReverseRelation["ComprehensiveScore"]
    
    class Meta:
        table = "students"
        table_description = "学生信息表"
    
    def __str__(self):
        return f"{self.name}({self.id})"


class AcademicScore(Model):
    """学业成绩模型（课程成绩）"""
    id = fields.IntField(pk=True)
    
    # 基本信息（冗余字段，方便查询）
    student_name = fields.CharField(max_length=100, description="姓名")
    college = fields.CharField(max_length=100, null=True, description="学院")
    grade = fields.CharField(max_length=20, null=True, description="年级")
    major = fields.CharField(max_length=100, null=True, description="专业")
    class_name = fields.CharField(max_length=50, null=True, description="班级")
    
    # 成绩信息
    total_score = fields.FloatField(default=0.0, description="总分")
    total_required_credits = fields.FloatField(default=0.0, description="总应获得学分")
    course_count = fields.IntField(default=0, description="门数")
    total_credits = fields.FloatField(default=0.0, description="总学分")
    earned_credits = fields.FloatField(default=0.0, description="获得学分")
    failed_credits = fields.FloatField(default=0.0, description="不及格学分")
    
    # 通过率和平均分
    pass_rate = fields.FloatField(default=0.0, description="通过率（%）")
    arithmetic_average = fields.FloatField(default=0.0, description="算术平均分")
    arithmetic_average_rank = fields.IntField(null=True, description="算术平均分排名")
    
    # 学分加权平均分
    weighted_average = fields.FloatField(default=0.0, description="学分加权平均分")
    weighted_average_rank = fields.IntField(null=True, description="学分加权平均分排名")
    
    # 绩点相关
    average_gpa = fields.FloatField(default=0.0, description="平均绩点")
    average_gpa_rank = fields.IntField(null=True, description="平均绩点排名")
    average_credit_gpa = fields.FloatField(default=0.0, description="平均学分绩点")
    average_credit_gpa_rank = fields.IntField(null=True, description="平均学分绩点排名")
    credit_gpa_sum = fields.FloatField(default=0.0, description="学分绩点和")
    credit_gpa_sum_rank = fields.IntField(null=True, description="学分绩点和排名")
    
    # 其他统计
    failed_course_count = fields.IntField(default=0, description="不及格门次")
    
    # 学期信息
    semester = fields.CharField(max_length=20, null=True, description="学期，如：2024-1")
    academic_year = fields.CharField(max_length=20, null=True, description="学年，如：2024-2025")
    
    # 备注和详细信息
    remarks = fields.TextField(null=True, description="备注")
    details = fields.JSONField(null=True, description="详细课程成绩信息")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # 关联关系
    student: fields.ForeignKeyRelation[Student] = fields.ForeignKeyField(
        "models.Student", related_name="academic_scores"
    )
    
    class Meta:
        table = "academic_scores"
        table_description = "学业成绩表"
        # 确保同一学生在同一学期只有一条记录
        unique_together = (("student_id", "semester", "academic_year"),)
    
    def __str__(self):
        return f"AcademicScore({self.student_id}, {self.student_name}, {self.semester})"


class ComprehensiveScoreConfig(Model):
    """综测成绩配置模型"""
    id = fields.IntField(pk=True)
    
    # 配置名称和描述
    name = fields.CharField(max_length=100, description="配置名称")
    description = fields.TextField(null=True, description="配置描述")
    
    # A/B/C类材料权重配置（总和应为100）
    a_weight = fields.FloatField(default=20.0, description="A类材料权重（%）")
    b_weight = fields.FloatField(default=70.0, description="B类材料（学习成绩）权重（%）")
    c_weight = fields.FloatField(default=10.0, description="C类材料权重（%）")
    
    # B类材料（学习成绩）字段选择
    # 可选值：arithmetic_average, weighted_average, average_gpa, average_credit_gpa, credit_gpa_sum
    academic_score_field = fields.CharField(
        max_length=50,
        default="weighted_average",
        description="学业成绩使用的字段"
    )
    
    # 学业成绩转换配置
    # 如果学业成绩是GPA（0-4分制），需要转换为百分制
    academic_score_scale = fields.FloatField(
        default=1.0,
        description="学业成绩缩放系数（GPA转百分制时用25）"
    )
    
    # 是否启用
    is_active = fields.BooleanField(default=True, description="是否启用此配置")
    is_default = fields.BooleanField(default=False, description="是否为默认配置")
    
    # 适用范围
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


class Certificate(Model):
    """证书模型"""
    id = fields.IntField(pk=True)
    
    student_id = fields.CharField(max_length=50, description="学生ID")
    file_id = fields.CharField(max_length=50, null=True, description="关联文件ID")
    filename = fields.CharField(max_length=255, description="文件名")
    file_path = fields.CharField(max_length=500, null=True, description="文件路径")
    
    certificate_type = fields.CharField(max_length=20, null=True, description="证书类型：四级、六级、竞赛、活动等")
    title = fields.CharField(max_length=255, null=True, description="证书标题")
    level = fields.CharField(max_length=100, null=True, description="证书级别：国家级、省级、校级、院级")
    issuer = fields.CharField(max_length=255, null=True, description="颁发机构")
    issue_date = fields.CharField(max_length=50, null=True, description="颁发日期")
    raw_text = fields.TextField(null=True, description="OCR原始文本")
    
    category = fields.CharField(max_length=10, default="C", description="证书类别: A或C")
    sub_category = fields.CharField(max_length=10, null=True, description="子类别: C1-科技类, C2-体育类, C3-文化类, C4-创新创业")
    score = fields.FloatField(default=0.0, description="证书分数")
    classification_reason = fields.TextField(null=True, description="分类原因")
    
    status = fields.CharField(
        max_length=20, 
        default="pending", 
        description="状态: pending(待审核), approved(已通过), rejected(已拒绝)"
    )
    reviewed_by = fields.CharField(max_length=50, null=True, description="审核人")
    reviewed_at = fields.DatetimeField(null=True, description="审核时间")
    review_comment = fields.TextField(null=True, description="审核意见")
    
    ocr_result = fields.JSONField(null=True, description="OCR识别结果")
    certificate_info = fields.JSONField(null=True, description="证书详细信息")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "certificates"
        table_description = "证书表"
        indexes = [("student_id",), ("category",), ("status",), ("sub_category",)]
    
    def __str__(self):
        return f"Certificate({self.student_id}, {self.title}, {self.category})"


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


class UploadRecord(Model):
    """上传记录模型 - 追踪文件上传历史"""
    id = fields.IntField(pk=True)
    
    file_id = fields.CharField(max_length=50, description="关联文件ID")
    file_name = fields.CharField(max_length=255, description="文件名")
    file_type = fields.CharField(max_length=50, description="文件类型: score_sheet, certificate, template")
    
    upload_by = fields.CharField(max_length=50, description="上传者")
    upload_role = fields.CharField(max_length=20, default="student", description="上传者角色")
    
    academic_year = fields.CharField(max_length=20, null=True, description="学年")
    semester = fields.CharField(max_length=20, null=True, description="学期")
    class_id = fields.CharField(max_length=50, null=True, description="班级ID")
    
    status = fields.CharField(max_length=20, default="pending", description="状态: pending, processing, completed, failed")
    processed_count = fields.IntField(default=0, description="处理成功数量")
    failed_count = fields.IntField(default=0, description="处理失败数量")
    
    error_message = fields.TextField(null=True, description="错误信息")
    processing_log = fields.TextField(null=True, description="处理日志")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    processed_at = fields.DatetimeField(null=True, description="处理完成时间")
    
    class Meta:
        table = "upload_records"
        table_description = "上传记录表"
        indexes = [("upload_by",), ("file_type",), ("status",)]
    
    def __str__(self):
        return f"UploadRecord({self.file_name}, {self.status})"