#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户相关模型
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
    
    def __str__(self):
        return f"User({self.username}, {self.role})"
