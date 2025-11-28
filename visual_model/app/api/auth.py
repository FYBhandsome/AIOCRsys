#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API路由 - 包含登录、注册、密码重置等功能
"""
from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.models.auth import (
    UserLogin, Token, TokenData, UserCreate, UserResponse,
    PasswordResetRequest, PasswordResetConfirm, PasswordChange
)
from app.models.tortoise_models import User
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.auth_middleware import get_current_user
from app.core.email_service import email_service, generate_reset_token, generate_verification_code
from app.core.logger import logger
from config import settings


router = APIRouter(prefix="/auth", tags=["认证"])


# 模拟用户数据库（兼容性保留，实际使用数据库）
# 密码为: password123
MOCK_USERS = {
    "student1": {
        "id": "s001",
        "username": "student1",
        "password_hash": get_password_hash("password123"),
        "role": "student",
        "real_name": "张三",
        "student_id": "2021001",
        "class_id": "cs2021"
    },
    "teacher1": {
        "id": "t001",
        "username": "teacher1",
        "password_hash": get_password_hash("password123"),
        "role": "teacher",
        "real_name": "李老师"
    },
    "admin": {
        "id": "a001",
        "username": "admin",
        "password_hash": get_password_hash("admin123"),
        "role": "admin",
        "real_name": "管理员"
    }
}


@router.post("/register", response_model=Dict[str, str])
async def register(user_create: UserCreate):
    """用户注册
    
    创建新用户账号
    """
    try:
        # 检查用户名是否已存在
        existing_user = await User.filter(username=user_create.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if user_create.email:
            existing_email = await User.filter(email=user_create.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )
        
        # 检查学号是否已存在（如果提供）
        if user_create.student_id:
            existing_student = await User.filter(student_id=user_create.student_id).first()
            if existing_student:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="学号已被注册"
                )
        
        # 创建新用户
        user = await User.create(
            username=user_create.username,
            email=user_create.email,
            password=get_password_hash(user_create.password),
            role=user_create.role,
            real_name=user_create.real_name,
            student_id=user_create.student_id,
            class_id=user_create.class_id,
            is_active=True,
            is_email_verified=False
        )
        
        logger.info(f"新用户注册成功: {user.username} (角色: {user.role})")
        
        # 如果提供了邮箱且启用了邮件服务，发送验证邮件
        if user_create.email and settings.EMAIL_ENABLED:
            # 生成验证令牌
            verification_token = generate_reset_token()
            user.reset_token = verification_token
            user.reset_token_expires = datetime.utcnow() + timedelta(days=1)
            await user.save()
            
            # 发送验证邮件
            verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            await email_service.send_verification_email(
                user_create.email,
                user.username,
                verification_link
            )
            logger.info(f"验证邮件已发送至: {user_create.email}")
        
        return {
            "message": "注册成功",
            "username": user.username,
            "user_id": str(user.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """用户登录
    
    获取JWT访问令牌
    """
    try:
        # 先尝试从数据库查找
        user = await User.filter(username=user_login.username).first()
        
        # 如果数据库中没有，则从模拟数据中查找（向后兼容）
        if not user:
            mock_user = MOCK_USERS.get(user_login.username)
            if not mock_user or not verify_password(user_login.password, mock_user["password_hash"]):
                logger.warning(f"登录失败: 用户名或密码错误 - {user_login.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 使用模拟用户数据
            user_data = {
                "user_id": mock_user["id"],
                "username": mock_user["username"],
                "role": mock_user["role"]
            }
        else:
            # 验证密码
            if not verify_password(user_login.password, user.password):
                logger.warning(f"登录失败: 密码错误 - {user_login.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 检查账号是否激活
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="账号已被禁用，请联系管理员"
                )
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            await user.save()
            
            user_data = {
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role
            }
        
        # 创建JWT令牌
        access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        access_token = create_access_token(
            data=user_data,
            expires_delta=access_token_expires
        )
        
        logger.info(f"用户登录成功: {user_data['username']} (角色: {user_data['role']})")
        
        return Token(
            access_token=access_token,
            expires_in=int(access_token_expires.total_seconds())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """获取当前登录用户信息"""
    # 开发模式：如果是默认开发用户，直接返回用户信息
    if settings.DISABLE_AUTH and current_user.username.startswith("dev_"):
        logger.info(f"开发模式：返回默认用户信息 - {current_user.username}")
        return {
            "id": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role,
            "real_name": f"开发测试用户({current_user.role})"
        }
    
    try:
        # 先从数据库查找
        user = await User.filter(username=current_user.username).first()
        
        if user:
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "real_name": user.real_name,
                "student_id": user.student_id,
                "class_id": user.class_id,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified
            }
        
        # 从模拟数据库获取完整用户信息（向后兼容）
        mock_user = MOCK_USERS.get(current_user.username)
        
        if not mock_user:
            logger.error(f"用户不存在: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        logger.info(f"返回用户信息: {current_user.username}")
        return {
            "id": mock_user["id"],
            "username": mock_user["username"],
            "role": mock_user["role"],
            "real_name": mock_user.get("real_name"),
            "student_id": mock_user.get("student_id"),
            "class_id": mock_user.get("class_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )

# 请求密码重置
@router.post("/password/reset-request")
async def request_password_reset(request: PasswordResetRequest):
    """请求密码重置
    
    发送验证码到邮箱（有效期2分钟）
    """
    try:
        # 查找用户
        user = await User.filter(email=request.email).first()
        
        # 无论用户是否存在，都返回成功（安全考虑，不泄露用户信息）
        if not user:
            logger.warning(f"密码重置请求: 邮箱不存在 - {request.email}")
            return {
                "message": "如果该邮箱已注册，您将收到验证码邮件"
            }
        
        # 检查邮件服务是否启用
        if not settings.EMAIL_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="邮件服务未启用，请联系管理员"
            )
        
        # 检查是否已有有效的验证码（2分钟内）
        now = datetime.utcnow()
        if user.verification_code and user.code_expires_at and user.code_expires_at > now:
            # 还有有效的验证码，重新发送相同的验证码
            verification_code = user.verification_code
            logger.info(f"重新发送现有验证码: {user.email}")
        else:
            # 生成新的6位验证码
            verification_code = generate_verification_code()
            user.verification_code = verification_code
            user.code_expires_at = now + timedelta(minutes=2)
            await user.save()
            logger.info(f"生成新验证码: {user.email}")
        
        # 发送验证码邮件
        await email_service.send_verification_code_email(
            user.email,
            user.username,
            verification_code
        )
        
        logger.info(f"验证码邮件已发送: {user.email}")
        
        return {
            "message": "如果该邮箱已注册，您将收到验证码邮件",
            "expires_in": 120  # 2分钟 = 120秒
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码重置请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码重置请求失败: {str(e)}"
        )

# 确认密码重置
@router.post("/password/reset-confirm")
async def confirm_password_reset(confirm: PasswordResetConfirm):
    """确认密码重置
    
    使用验证码重置密码
    """
    try:
        # 查找用户
        user = await User.filter(email=confirm.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱不存在"
            )
        
        # 检查验证码是否存在
        if not user.verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先获取验证码"
            )
        
        # 检查验证码是否过期
        if not user.code_expires_at or user.code_expires_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期，请重新获取"
            )
        
        # 验证验证码
        if user.verification_code != confirm.verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )
        
        # 更新密码
        user.password = get_password_hash(confirm.new_password)
        # 清除验证码
        user.verification_code = None
        user.code_expires_at = None
        await user.save()
        
        logger.info(f"密码重置成功: {user.username} ({user.email})")
        
        return {
            "message": "密码重置成功，请使用新密码登录"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码重置确认失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码重置失败: {str(e)}"
        )

# 修改密码
@router.post("/password/change")
async def change_password(
    password_change: PasswordChange,
    current_user: TokenData = Depends(get_current_user)
):
    """修改密码
    
    需要提供旧密码
    """
    try:
        # 查找用户
        user = await User.filter(username=current_user.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证旧密码
        if not verify_password(password_change.old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 更新密码
        user.password = get_password_hash(password_change.new_password)
        await user.save()
        
        logger.info(f"用户修改密码成功: {user.username}")
        
        return {
            "message": "密码修改成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改密码失败: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """用户登出
    
    客户端应删除本地存储的令牌
    """
    logger.info(f"用户登出: {current_user.username}")
    return {"message": "登出成功"}
