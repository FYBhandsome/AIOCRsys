#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证中间件和依赖注入
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token
from app.models.auth import TokenData, UserRole
from app.core.logger import logger
from config import settings


# HTTP Bearer Token方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenData:
    """获取当前用户
    
    从Authorization头中提取JWT令牌并验证
    
    开发模式：如果DISABLE_AUTH=True，返回默认管理员用户（无需认证）
    """
    # 开发测试模式：禁用认证
    if settings.DISABLE_AUTH:
        logger.warning("⚠️  认证已禁用 - 使用默认管理员用户（仅用于开发测试）")
        return TokenData(
            user_id="dev_admin",
            username="dev_admin",
            role=UserRole.ADMIN
        )
    
    # 生产模式：正常认证
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


def require_roles(allowed_roles: List[UserRole]):
    """角色权限检查装饰器
    
    Args:
        allowed_roles: 允许的角色列表
        
    Returns:
        依赖函数
    """
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"用户 {current_user.username} (角色:{current_user.role}) "
                f"尝试访问需要 {allowed_roles} 权限的资源"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下角色之一: {[r.value for r in allowed_roles]}"
            )
        return current_user
    
    return role_checker


# 常用角色依赖
async def get_student_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """获取学生用户"""
    # 开发模式：管理员可以访问所有角色
    if settings.DISABLE_AUTH and current_user.role == UserRole.ADMIN:
        return TokenData(user_id="dev_student", username="dev_student", role=UserRole.STUDENT)
    
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅限学生访问"
        )
    return current_user


async def get_teacher_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """获取教师用户"""
    # 开发模式：管理员可以访问所有角色
    if settings.DISABLE_AUTH and current_user.role == UserRole.ADMIN:
        return TokenData(user_id="dev_teacher", username="dev_teacher", role=UserRole.TEACHER)
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅限教师访问"
        )
    return current_user


async def get_admin_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """获取管理员用户"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅限管理员访问"
        )
    return current_user


async def get_teacher_or_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """获取教师或管理员用户"""
    # 开发模式：管理员可以访问
    if settings.DISABLE_AUTH and current_user.role == UserRole.ADMIN:
        return current_user
    
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅限教师或管理员访问"
        )
    return current_user

