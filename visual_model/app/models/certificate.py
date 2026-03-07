#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书相关模型
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional


class Certificate(Model):
    """证书模型 - 存储证书基本信息"""
    id = fields.IntField(pk=True)
    
    student_id = fields.CharField(max_length=50, description="学生ID（学号）")
    
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
    
    certificate_id = fields.IntField(description="关联证书ID")
    student_id = fields.CharField(max_length=50, description="学生ID（冗余字段，便于查询）")
    
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
