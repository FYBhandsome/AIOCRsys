#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.models.auth import TokenData
from app.core.auth_middleware import get_current_user
from app.services.rag_client import get_rag_client
from app.core.logger import logger
from config import settings


router = APIRouter(prefix="/ai", tags=["AI助手"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    userId: Optional[str] = None
    chat_history: Optional[List[Dict[str, str]]] = None
    use_rag: bool = True


class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str
    success: bool = True
    timestamp: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """AI助手对话接口
    
    通过RAG系统进行智能对话，支持综测规则查询
    """
    try:
        if not settings.RAG_ENABLED:
            return ChatResponse(
                reply="AI助手功能当前未启用。请联系管理员开启RAG系统。",
                success=False
            )
        
        # 准备学生信息
        student_info = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role
        }
        
        # 调用RAG系统进行对话
        rag_client = get_rag_client()
        result = await rag_client.chat(
            message=request.message,
            use_rag=request.use_rag,
            chat_history=request.chat_history or [],
            student_info=student_info
        )
        
        logger.info(f"用户 {current_user.username} 进行AI对话")
        
        # 返回AI回复
        return ChatResponse(
            reply=result.get("reply", "抱歉，我现在无法回答。"),
            success=result.get("success", True),
            timestamp=result.get("timestamp")
        )
    
    except Exception as e:
        logger.error(f"AI对话失败: {e}", exc_info=True)
        return ChatResponse(
            reply="抱歉，AI助手暂时无法响应。请稍后再试。",
            success=False
        )

