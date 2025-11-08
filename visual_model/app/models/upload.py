#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件上传相关数据模型 - 重构版本
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

# ============================================================================
# 基础响应模型
# ============================================================================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

# ============================================================================
# 文件上传相关模型
# ============================================================================

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: str
    filename: str
    file_size: int
    message: str
    upload_time: datetime = Field(default_factory=datetime.now)

class OCRResult(BaseModel):
    """OCR识别结果模型"""
    file_id: str
    filename: str
    file_size: int
    recognition_results: List[Dict[str, Any]]
    certificate_info: Optional[Dict[str, Any]] = None
    processed_at: datetime = Field(default_factory=datetime.now)

class FileDeleteResponse(BaseModel):
    """删除文件响应模型"""
    file_id: str
    message: str
    deleted_at: datetime = Field(default_factory=datetime.now)