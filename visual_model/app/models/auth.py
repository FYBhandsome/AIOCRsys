#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证相关数据模型
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """用户角色枚举"""
    STUDENT = "student"      # 学生
    TEACHER = "teacher"      # 教师
    ADMIN = "admin"         # 管理员


class Token(BaseModel):
    """JWT令牌响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 过期时间（秒）


class TokenData(BaseModel):
    """JWT令牌数据"""
    user_id: str
    username: str
    role: UserRole
    exp: Optional[datetime] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.STUDENT
    real_name: Optional[str] = None
    student_id: Optional[str] = None  # 学号（学生）
    class_id: Optional[str] = None    # 班级ID（学生）


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    real_name: Optional[str] = None
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: Optional[str] = None
    role: UserRole
    real_name: Optional[str] = None
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class PasswordResetRequest(BaseModel):
    """密码重置请求（发送验证码）"""
    email: EmailStr = Field(..., description="注册邮箱")


class PasswordResetConfirm(BaseModel):
    """密码重置确认（使用验证码）"""
    email: EmailStr = Field(..., description="邮箱")
    verification_code: str = Field(..., min_length=6, max_length=6, description="6位验证码")
    new_password: str = Field(..., min_length=6, description="新密码")


class PasswordResetConfirmOld(BaseModel):
    """密码重置确认（旧版本，使用token）"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, description="新密码")


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class EmailVerify(BaseModel):
    """邮箱验证"""
    token: str = Field(..., description="验证令牌")
