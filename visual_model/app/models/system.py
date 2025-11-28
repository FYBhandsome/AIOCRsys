#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统设置相关数据模型
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# 系统设置相关模型
# ============================================================================

class SystemSettingsBase(BaseModel):
    """系统设置基础模型"""
    system_name: str = Field(default="综测系统", description="系统名称")
    max_upload_size: int = Field(default=10485760, description="最大上传文件大小（字节）")
    allowed_file_types: List[str] = Field(
        default=[".pdf", ".docx", ".doc", ".txt", ".md", ".jpg", ".png"],
        description="允许上传的文件类型"
    )
    ai_model: str = Field(default="gpt-3.5-turbo", description="AI模型")
    ai_temperature: float = Field(default=0.7, description="AI温度参数")
    ai_max_tokens: int = Field(default=1000, description="AI最大token数")
    ai_system_prompt: str = Field(
        default="你是一个综测系统助手，请根据提供的信息回答问题。",
        description="AI系统提示"
    )


class SystemSettingsCreate(SystemSettingsBase):
    """创建系统设置模型"""
    pass


class SystemSettingsUpdate(SystemSettingsBase):
    """更新系统设置模型"""
    system_name: Optional[str] = None
    max_upload_size: Optional[int] = None
    allowed_file_types: Optional[List[str]] = None
    ai_model: Optional[str] = None
    ai_temperature: Optional[float] = None
    ai_max_tokens: Optional[int] = None
    ai_system_prompt: Optional[str] = None


class SystemSettings(SystemSettingsBase):
    """系统设置模型"""
    id: str = Field(description="设置ID")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        from_attributes = True


class SystemSettingsResponse(SystemSettings):
    """系统设置响应模型"""
    pass