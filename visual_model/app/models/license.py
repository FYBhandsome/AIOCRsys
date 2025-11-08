#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
授权验证相关数据模型
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class LicenseVerifyRequest(BaseModel):
    """授权验证请求"""
    license: str = Field(..., description="授权码字符串")
    token: str = Field(..., description="Token验证码")
    prefer_offline: bool = Field(True, description="是否优先使用离线验证")


class LicenseVerifyResponse(BaseModel):
    """授权验证响应"""
    valid: bool = Field(..., description="验证是否成功")
    customer: Optional[str] = Field(None, description="客户名称")
    expires_at: Optional[str] = Field(None, description="过期时间")
    issued_at: Optional[str] = Field(None, description="签发时间")
    verification_mode: Optional[str] = Field(None, description="验证模式: offline/online")
    key_source: Optional[str] = Field(None, description="密钥来源: default/remote")
    reason: Optional[str] = Field(None, description="失败原因")
    offline_error: Optional[str] = Field(None, description="离线验证错误信息")
    online_error: Optional[str] = Field(None, description="在线验证错误信息")


class TokenResponse(BaseModel):
    """Token响应"""
    token: Optional[str] = Field(None, description="Token验证码")
    reason: Optional[str] = Field(None, description="失败原因")


class SystemInfoResponse(BaseModel):
    """系统信息响应"""
    mac_addresses: list = Field(..., description="MAC地址列表")
    current_time: str = Field(..., description="当前时间")
    network_status: dict = Field(..., description="网络状态")
    public_key_available: bool = Field(..., description="公钥是否可用")
    key_source: str = Field(..., description="密钥来源")
    key_scheme: str = Field(..., description="密钥方案")


class NetworkStatusResponse(BaseModel):
    """网络状态响应"""
    network_status: dict = Field(..., description="网络状态详情")
    recommended_mode: str = Field(..., description="推荐的验证模式")
    timestamp: str = Field(..., description="时间戳")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="健康状态: healthy/unhealthy")
    mac_addresses_available: Optional[bool] = Field(None, description="MAC地址是否可用")
    public_key_available: Optional[bool] = Field(None, description="公钥是否可用")
    key_source: Optional[str] = Field(None, description="密钥来源")
    key_scheme: Optional[str] = Field(None, description="密钥方案")
    generator_status: Optional[str] = Field(None, description="生成器状态")
    network_status: Optional[dict] = Field(None, description="网络状态")
    recommended_verification_mode: Optional[str] = Field(None, description="推荐的验证模式")
    error: Optional[str] = Field(None, description="错误信息")


class PersistentLicenseCheckResponse(BaseModel):
    """持久化授权检查响应"""
    valid: bool = Field(..., description="授权是否有效")
    customer: Optional[str] = Field(None, description="客户名称")
    expires_at: Optional[str] = Field(None, description="过期时间")
    issued_at: Optional[str] = Field(None, description="签发时间")
    verification_mode: Optional[str] = Field(None, description="验证模式")
    key_source: Optional[str] = Field(None, description="密钥来源")
    key_scheme: Optional[str] = Field(None, description="密钥方案")
    reason: Optional[str] = Field(None, description="失败原因")


class PersistentLicenseSaveRequest(BaseModel):
    """保存持久化授权请求"""
    license: str = Field(..., description="授权码字符串")
    token: str = Field("", description="Token验证码（可选）")


class PersistentLicenseSaveResponse(BaseModel):
    """保存持久化授权响应"""
    success: bool = Field(..., description="保存是否成功")
    message: Optional[str] = Field(None, description="成功消息")
    reason: Optional[str] = Field(None, description="失败原因")


class StorageInfoResponse(BaseModel):
    """存储信息响应"""
    storage_dir: str = Field(..., description="存储目录路径")
    storage_dir_exists: bool = Field(..., description="存储目录是否存在")
    license_file_exists: bool = Field(..., description="授权文件是否存在")
    license_file_size: int = Field(..., description="授权文件大小(字节)")
    verification_file_exists: bool = Field(..., description="验证记录文件是否存在")
    verification_file_size: int = Field(..., description="验证记录文件大小(字节)")
    verification_records_count: int = Field(..., description="验证记录数量")
    timestamp: str = Field(..., description="时间戳")
    error: Optional[str] = Field(None, description="错误信息")


class OnlineVerifyRequest(BaseModel):
    """在线验证请求"""
    license: str = Field(..., description="授权码字符串")

