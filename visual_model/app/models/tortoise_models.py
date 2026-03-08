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


class ClassStudent(Model):
    """班级学生关联模型"""
    id = fields.IntField(pk=True)
    class_id = fields.ForeignKeyField(
        "models.Class", 
        related_name="students", 
        description="班级"
    )
    student = fields.ForeignKeyField(
        "models.Student", 
        related_name="classes", 
        description="学生"
    )
    
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "class_students"
        table_description = "班级学生关联表"
        unique_together = ("class_id", "student_id")
    
    def __str__(self):
        return f"ClassStudent({self.class_id}, {self.student_id})"


class User(Model):
    """用户模型"""
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=255, unique=True, null=True, description="邮箱")
    password = fields.CharField(max_length=255, description="密码（加密存储）")
    role = fields.CharField(max_length=20, default="student", description="角色：student, teacher, admin")
    
    student_id = fields.CharField(max_length=50, null=True, unique=True, description="学号")
    real_name = fields.CharField(max_length=100, null=True, description="真实姓名")
    class_id = fields.CharField(max_length=50, null=True, description="班级ID")
    
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_email_verified = fields.BooleanField(default=False, description="邮箱是否验证")
    
    reset_token = fields.CharField(max_length=255, null=True, description="密码重置令牌")
    reset_token_expires = fields.DatetimeField(null=True, description="重置令牌过期时间")
    
    verification_code = fields.CharField(max_length=10, null=True, description="验证码")
    code_expires_at = fields.DatetimeField(null=True, description="验证码过期时间")
    
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    extra_info = fields.JSONField(null=True, description="其他信息")
    
    class Meta:
        table = "users"
        table_description = "用户信息表"
        indexes = [
            ("class_id",),
            ("role",),
            ("student_id",),
            ("is_active",),
            ("class_id", "role"),
        ]
    
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
    
    total_score = fields.FloatField(default=0.0, description="综测总成绩")
    
    dormitory_number = fields.CharField(max_length=50, null=True, description="宿舍编号")
    dormitory_score = fields.FloatField(null=True, description="宿舍成绩")
    
    physical_test_score = fields.FloatField(null=True, description="体测成绩")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    academic_scores: fields.ReverseRelation["AcademicScore"]
    comprehensive_scores: fields.ReverseRelation["ComprehensiveScore"]
    
    class Meta:
        table = "students"
        table_description = "学生信息表"
        indexes = [
            ("class_name",),
            ("grade",),
            ("major",),
            ("college",),
            ("class_name", "grade"),
            ("name",),
        ]
    
    def __str__(self):
        return f"{self.name}({self.id})"


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
    
    student: fields.ForeignKeyRelation[Student] = fields.ForeignKeyField(
        "models.Student", related_name="academic_scores", null=True
    )
    
    class Meta:
        table = "academic_scores"
        table_description = "学业成绩表"
        unique_together = (("student_id", "semester", "academic_year"),)
        indexes = [
            ("student_id",),
            ("class_name",),
            ("academic_year",),
            ("semester",),
            ("academic_year", "semester"),
            ("class_name", "academic_year"),
            ("weighted_average",),
            ("average_gpa",),
        ]
    
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
    
    student_name = fields.CharField(max_length=100, null=True, description="姓名")
    class_name = fields.CharField(max_length=50, null=True, description="班级")
    major = fields.CharField(max_length=100, null=True, description="专业")
    
    # A类材料成绩（思想道德素质）
    a_total_score = fields.FloatField(default=0.0, description="A类材料总成绩")
    a1_score = fields.FloatField(default=0.0, description="A1类成绩")
    a2_score = fields.FloatField(default=0.0, description="A2类成绩")
    a3_score = fields.FloatField(default=0.0, description="A3类成绩")
    a_weighted_score = fields.FloatField(default=0.0, description="A类加权成绩(20%)")
    
    # B类材料成绩（学习成绩)
    b_raw_score = fields.FloatField(default=0.0, description="B类原始成绩")
    b_weighted_score = fields.FloatField(default=0.0, description="B类加权成绩(70%)")
    b_total_score = fields.FloatField(default=0.0, description="B类总成绩（兼容字段）")
    b_total_score = fields.FloatField(default=0.0, description="B类总成绩（学业成绩）")
    
    # C类材料成绩（素质拓展）
    c_total_score = fields.FloatField(default=0.0, description="C类材料总成绩")
    c1_score = fields.FloatField(default=0.0, description="C1类成绩-科技竞赛")
    c2_score = fields.FloatField(default=0.0, description="C2类成绩-体育竞技")
    c3_score = fields.FloatField(default=0.0, description="C3类成绩-文化竞赛")
    c4_score = fields.FloatField(default=0.0, description="C4类成绩-创新创业")
    c_weighted_score = fields.FloatField(default=0.0, description="C类加权成绩(10%)")
    
    # 综测总成绩
    total_score = fields.FloatField(default=0.0, description="综测总成绩")
    ranking = fields.IntField(null=True, description="班级排名")
    
    # 学期信息
    semester = fields.CharField(max_length=20, description="学期，如：1")
    academic_year = fields.CharField(max_length=20, description="学年，如：2024-2025")
    
    # 配置关联
    config_id = fields.IntField(null=True, description="使用的配置ID")
    
    # 学生关联
    student = fields.ForeignKeyField("models.Student", related_name="comprehensive_scores", description="关联学生")
    
    # 来源追踪
    source_file = fields.CharField(max_length=255, null=True, description="来源文件名")
    source_type = fields.CharField(max_length=20, default="comprehensive_table", description="来源类型")
    
    # 备注和详细信息
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
    """证书模型 - 存储证书基本信息"""
    id = fields.IntField(pk=True)
    
    student_id = fields.CharField(max_length=50, description="学生ID（学号）")
    filename = fields.CharField(max_length=255, null=True, description="原始文件名")
    
    certificate_no = fields.CharField(max_length=100, null=True, description="证书编号")
    certificate_type = fields.CharField(max_length=50, null=True, description="证书类型：四级、六级、竞赛、活动、荣誉等")
    title = fields.CharField(max_length=255, null=True, description="证书标题/名称")
    level = fields.CharField(max_length=50, null=True, description="证书级别：国家级、省级、市级、校级、院级")
    issuer = fields.CharField(max_length=255, null=True, description="颁发机构")
    issue_date = fields.CharField(max_length=50, null=True, description="颁发日期")
    expiry_date = fields.CharField(max_length=50, null=True, description="有效期至")
    
    category = fields.CharField(max_length=10, default="C", description="证书类别: A-思想道德, C-素质拓展")
    sub_category = fields.CharField(max_length=10, null=True, description="子类别: C1-科技类, C2-体育类, C3-文化类, C4-创新创业")
    score = fields.FloatField(default=0.0, description="证书加分分数")
    classification_reason = fields.TextField(null=True, description="分类原因/评分依据")
    
    raw_text = fields.TextField(null=True, description="OCR识别原始文本")
    ocr_result = fields.JSONField(null=True, description="OCR识别详细结果")
    certificate_info = fields.JSONField(null=True, description="证书结构化信息")
    
    status = fields.CharField(
        max_length=20, 
        default="pending", 
        description="状态: pending(待审核), approved(已通过), rejected(已拒绝), cancelled(已取消)"
    )
    reviewed_by = fields.CharField(max_length=50, null=True, description="审核人")
    reviewed_at = fields.DatetimeField(null=True, description="审核时间")
    review_comment = fields.TextField(null=True, description="审核意见")
    
    image_count = fields.IntField(default=0, description="关联图片数量")
    primary_image_id = fields.IntField(null=True, description="主图片ID")
    
    source = fields.CharField(max_length=20, default="upload", description="来源: upload(上传), import(导入), manual(手动录入)")
    upload_batch_id = fields.CharField(max_length=50, null=True, description="上传批次ID")
    
    is_valid = fields.BooleanField(default=True, description="是否有效")
    invalid_reason = fields.TextField(null=True, description="无效原因")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "certificates"
        table_description = "证书基本信息表"
        indexes = [
            ("student_id",),
            ("category",),
            ("sub_category",),
            ("status",),
            ("certificate_type",),
            ("level",),
            ("issue_date",),
            ("student_id", "status"),
        ]
    
    def __str__(self):
        return f"Certificate({self.student_id}, {self.title}, {self.category})"


class CertificateImage(Model):
    """证书图片模型 - 存储证书的多张图片"""
    id = fields.IntField(pk=True)
    
    certificate = fields.ForeignKeyField(
        "models.Certificate", 
        related_name="images", 
        description="关联证书"
    )
    student = fields.ForeignKeyField(
        "models.Student", 
        related_name="certificate_images", 
        description="学生"
    )
    
    file_id = fields.CharField(max_length=50, null=True, description="文件管理ID")
    filename = fields.CharField(max_length=255, description="原始文件名")
    file_path = fields.CharField(max_length=500, description="文件存储路径")
    file_size = fields.IntField(default=0, description="文件大小(字节)")
    file_hash = fields.CharField(max_length=64, null=True, description="文件MD5哈希值")
    
    image_width = fields.IntField(null=True, description="图片宽度")
    image_height = fields.IntField(null=True, description="图片高度")
    image_format = fields.CharField(max_length=10, null=True, description="图片格式: jpg, png, pdf等")
    
    is_primary = fields.BooleanField(default=False, description="是否为主图片")
    image_order = fields.IntField(default=0, description="图片排序顺序")
    page_number = fields.IntField(null=True, description="页码（多页证书）")
    
    ocr_processed = fields.BooleanField(default=False, description="是否已进行OCR处理")
    ocr_text = fields.TextField(null=True, description="该图片OCR识别文本")
    ocr_result = fields.JSONField(null=True, description="该图片OCR详细结果")
    
    thumbnail_path = fields.CharField(max_length=500, null=True, description="缩略图路径")
    
    upload_ip = fields.CharField(max_length=50, null=True, description="上传IP地址")
    upload_device = fields.CharField(max_length=100, null=True, description="上传设备信息")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "certificate_images"
        table_description = "证书图片表"
        indexes = [
            ("certificate_id",),
            ("student_id",),
            ("file_hash",),
            ("is_primary",),
            ("certificate_id", "image_order"),
        ]
    
    def __str__(self):
        return f"CertificateImage({self.certificate_id}, {self.filename})"


class CertificateBatch(Model):
    """证书上传批次模型 - 追踪批量上传"""
    id = fields.IntField(pk=True)
    
    batch_id = fields.CharField(max_length=50, unique=True, description="批次唯一标识")
    student_id = fields.CharField(max_length=50, description="学生ID")
    
    total_count = fields.IntField(default=0, description="总上传数量")
    success_count = fields.IntField(default=0, description="成功处理数量")
    failed_count = fields.IntField(default=0, description="失败数量")
    
    status = fields.CharField(max_length=20, default="pending", description="状态: pending, processing, completed, failed")
    error_message = fields.TextField(null=True, description="错误信息")
    processing_log = fields.JSONField(null=True, description="处理日志")
    
    upload_ip = fields.CharField(max_length=50, null=True, description="上传IP")
    upload_device = fields.CharField(max_length=100, null=True, description="上传设备")
    
    started_at = fields.DatetimeField(null=True, description="开始处理时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "certificate_batches"
        table_description = "证书上传批次表"
        indexes = [
            ("batch_id",),
            ("student_id",),
            ("status",),
            ("created_at",),
        ]
    
    def __str__(self):
        return f"CertificateBatch({self.batch_id}, {self.student_id})"


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


class FileMetadata(Model):
    """文件元数据模型 - 统一管理所有文件"""
    id = fields.IntField(pk=True)
    
    file_id = fields.CharField(max_length=100, unique=True, description="文件唯一标识")
    original_filename = fields.CharField(max_length=255, description="原始文件名")
    stored_filename = fields.CharField(max_length=255, description="存储文件名")
    
    file_type = fields.CharField(max_length=50, description="文件类型: transcript, photo, certificate, template, result")
    file_category = fields.CharField(max_length=50, description="文件分类: score_sheet, id_photo, certificate_photo, comprehensive_result")
    mime_type = fields.CharField(max_length=100, null=True, description="MIME类型")
    file_extension = fields.CharField(max_length=20, null=True, description="文件扩展名")
    
    file_size = fields.IntField(default=0, description="文件大小(字节)")
    file_hash = fields.CharField(max_length=64, null=True, description="文件MD5哈希")
    
    storage_path = fields.CharField(max_length=500, description="存储路径")
    storage_directory = fields.CharField(max_length=255, description="存储目录")
    
    owner_id = fields.CharField(max_length=50, description="所有者ID(学号/工号)")
    owner_type = fields.CharField(max_length=20, default="student", description="所有者类型: student, teacher, admin")
    
    upload_batch_id = fields.CharField(max_length=50, null=True, description="上传批次ID")
    chunk_upload = fields.BooleanField(default=False, description="是否分片上传")
    chunk_count = fields.IntField(default=0, description="分片总数")
    chunk_uploaded = fields.IntField(default=0, description="已上传分片数")
    
    status = fields.CharField(max_length=20, default="active", description="状态: active, archived, deleted, corrupted")
    is_encrypted = fields.BooleanField(default=False, description="是否加密")
    is_public = fields.BooleanField(default=False, description="是否公开")
    
    access_count = fields.IntField(default=0, description="访问次数")
    download_count = fields.IntField(default=0, description="下载次数")
    
    last_accessed_at = fields.DatetimeField(null=True, description="最后访问时间")
    archived_at = fields.DatetimeField(null=True, description="归档时间")
    
    metadata = fields.JSONField(null=True, description="扩展元数据")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "file_metadata"
        table_description = "文件元数据表"
        indexes = [
            ("file_id",),
            ("owner_id",),
            ("file_type",),
            ("file_category",),
            ("status",),
            ("owner_id", "file_type"),
            ("created_at",),
        ]
    
    def __str__(self):
        return f"FileMetadata({self.file_id}, {self.original_filename})"


class FileChunk(Model):
    """文件分片模型 - 支持大文件分片上传"""
    id = fields.IntField(pk=True)
    
    file_id = fields.CharField(max_length=100, description="关联文件ID")
    chunk_index = fields.IntField(description="分片序号")
    chunk_hash = fields.CharField(max_length=64, null=True, description="分片MD5哈希")
    
    chunk_size = fields.IntField(default=0, description="分片大小(字节)")
    chunk_path = fields.CharField(max_length=500, null=True, description="分片存储路径")
    
    status = fields.CharField(max_length=20, default="pending", description="状态: pending, uploaded, merged, failed")
    upload_ip = fields.CharField(max_length=50, null=True, description="上传IP")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    uploaded_at = fields.DatetimeField(null=True, description="上传完成时间")
    
    class Meta:
        table = "file_chunks"
        table_description = "文件分片表"
        indexes = [("file_id",), ("file_id", "chunk_index")]
        unique_together = (("file_id", "chunk_index"),)
    
    def __str__(self):
        return f"FileChunk({self.file_id}, chunk_{self.chunk_index})"


class DownloadLog(Model):
    """下载日志模型 - 记录文件下载历史"""
    id = fields.IntField(pk=True)
    
    file_id = fields.CharField(max_length=100, description="文件ID")
    file_name = fields.CharField(max_length=255, description="文件名")
    
    downloader_id = fields.CharField(max_length=50, description="下载者ID")
    downloader_type = fields.CharField(max_length=20, description="下载者类型")
    downloader_ip = fields.CharField(max_length=50, null=True, description="下载IP")
    
    download_status = fields.CharField(max_length=20, default="success", description="下载状态: success, failed, denied")
    download_size = fields.IntField(default=0, description="下载大小(字节)")
    error_message = fields.TextField(null=True, description="错误信息")
    
    user_agent = fields.CharField(max_length=500, null=True, description="用户代理")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "download_logs"
        table_description = "下载日志表"
        indexes = [("file_id",), ("downloader_id",), ("created_at",)]
    
    def __str__(self):
        return f"DownloadLog({self.file_id}, {self.downloader_id})"


class FileAccessPermission(Model):
    """文件访问权限模型"""
    id = fields.IntField(pk=True)
    
    file_id = fields.CharField(max_length=100, description="文件ID")
    
    user_id = fields.CharField(max_length=50, null=True, description="用户ID")
    role_type = fields.CharField(max_length=20, null=True, description="角色类型: student, teacher, admin")
    
    permission_type = fields.CharField(max_length=20, description="权限类型: read, write, delete, download")
    
    granted_by = fields.CharField(max_length=50, null=True, description="授权人")
    granted_at = fields.DatetimeField(auto_now_add=True, description="授权时间")
    expires_at = fields.DatetimeField(null=True, description="过期时间")
    
    is_active = fields.BooleanField(default=True, description="是否有效")
    
    class Meta:
        table = "file_access_permissions"
        table_description = "文件访问权限表"
        indexes = [("file_id",), ("user_id",), ("role_type",)]
        unique_together = (("file_id", "user_id", "permission_type"),)
    
    def __str__(self):
        return f"FileAccessPermission({self.file_id}, {self.user_id}, {self.permission_type})"


class FileBackup(Model):
    """文件备份模型"""
    id = fields.IntField(pk=True)
    
    original_file_id = fields.CharField(max_length=100, description="原文件ID")
    backup_file_id = fields.CharField(max_length=100, description="备份文件ID")
    
    backup_path = fields.CharField(max_length=500, description="备份存储路径")
    backup_size = fields.IntField(default=0, description="备份大小(字节)")
    
    backup_type = fields.CharField(max_length=20, default="full", description="备份类型: full, incremental")
    backup_reason = fields.CharField(max_length=100, null=True, description="备份原因")
    
    status = fields.CharField(max_length=20, default="active", description="状态: active, archived, deleted")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "file_backups"
        table_description = "文件备份表"
        indexes = [("original_file_id",), ("backup_file_id",), ("created_at",)]
    
    def __str__(self):
        return f"FileBackup({self.original_file_id} -> {self.backup_file_id})"


class SystemSetting(Model):
    """系统设置模型"""
    id = fields.IntField(pk=True)
    
    setting_key = fields.CharField(max_length=100, unique=True, description="设置键")
    setting_value = fields.TextField(description="设置值(JSON)")
    setting_type = fields.CharField(max_length=20, default="string", description="设置类型: string, number, boolean, json")
    
    description = fields.CharField(max_length=255, null=True, description="设置描述")
    category = fields.CharField(max_length=50, default="general", description="设置分类")
    
    is_public = fields.BooleanField(default=False, description="是否公开(非管理员可见)")
    is_editable = fields.BooleanField(default=True, description="是否可编辑")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    updated_by = fields.CharField(max_length=50, null=True, description="最后更新人")
    
    class Meta:
        table = "system_settings"
        table_description = "系统设置表"
        indexes = [("setting_key",), ("category",)]
    
    def __str__(self):
        return f"SystemSetting({self.setting_key})"


class ChatHistory(Model):
    """对话历史模型"""
    id = fields.IntField(pk=True)
    
    user_id = fields.CharField(max_length=50, description="用户ID")
    session_id = fields.CharField(max_length=100, description="会话ID")
    
    role = fields.CharField(max_length=20, description="角色: user, assistant")
    content = fields.TextField(description="消息内容")
    
    message_type = fields.CharField(max_length=20, default="text", description="消息类型: text, image, file")
    metadata = fields.JSONField(null=True, description="元数据")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "chat_histories"
        table_description = "对话历史表"
        indexes = [("user_id",), ("session_id",), ("created_at",)]
    
    def __str__(self):
        return f"ChatHistory({self.user_id}, {self.role})"