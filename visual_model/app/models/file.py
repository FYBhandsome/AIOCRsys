#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件相关模型
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional


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
