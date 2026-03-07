#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统相关模型
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Optional


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
