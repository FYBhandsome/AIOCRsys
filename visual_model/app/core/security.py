#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具：JWT认证、密码加密等
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt

from app.core.logger import logger
from app.models.auth import TokenData, UserRole
from config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌
    
    Args:
        data: 要编码的数据（包含user_id, username, role）
        expires_delta: 过期时间
        
    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """解码JWT令牌
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        TokenData对象或None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        if user_id is None or username is None or role is None:
            return None
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=UserRole(role)
        )
    except JWTError as e:
        logger.warning(f"JWT解码失败: {e}")
        return None

