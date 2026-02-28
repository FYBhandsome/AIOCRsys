#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手API路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.models.auth import TokenData
from app.core.auth_middleware import get_current_user
from app.services.rag_client import get_rag_client
from app.core.logger import logger
from config import settings


router = APIRouter(prefix="/ai", tags=["AI助手"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息内容")
    userId: Optional[str] = Field(None, description="用户ID")
    chat_history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")
    use_rag: bool = Field(True, description="是否使用RAG检索")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str = Field(..., description="AI回复内容")
    success: bool = Field(True, description="是否成功")
    timestamp: Optional[str] = Field(None, description="时间戳")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="引用来源")


class AssistantMessageRequest(BaseModel):
    """AI助手消息请求模型"""
    question: str = Field(..., description="用户问题")
    userId: Optional[str] = Field(None, description="用户ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class AssistantMessageResponse(BaseModel):
    """AI助手消息响应模型"""
    response: str = Field(..., description="AI回复")
    success: bool = Field(True, description="是否成功")
    suggestions: Optional[List[str]] = Field(None, description="建议问题")


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """AI助手对话接口
    
    通过RAG系统进行智能对话，支持综测规则查询
    
    Args:
        request: 聊天请求，包含消息内容和可选的对话历史
        current_user: 当前登录用户
        
    Returns:
        ChatResponse: AI回复内容
    """
    try:
        if not settings.RAG_ENABLED:
            return ChatResponse(
                reply="AI助手功能当前未启用。请联系管理员开启RAG系统。",
                success=False,
                timestamp=datetime.now().isoformat()
            )
        
        student_info = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role
        }
        
        rag_client = get_rag_client()
        result = await rag_client.chat(
            message=request.message,
            use_rag=request.use_rag,
            chat_history=request.chat_history or [],
            student_info=student_info
        )
        
        logger.info(f"用户 {current_user.username} 进行AI对话: {request.message[:50]}...")
        
        return ChatResponse(
            reply=result.get("reply", "抱歉，我现在无法回答。"),
            success=result.get("success", True),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            sources=result.get("sources")
        )
    
    except Exception as e:
        logger.error(f"AI对话失败: {e}", exc_info=True)
        return ChatResponse(
            reply="抱歉，AI助手暂时无法响应。请稍后再试。",
            success=False,
            timestamp=datetime.now().isoformat()
        )


@router.post("/chat/stream")
async def ai_chat_stream(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """AI助手流式对话接口
    
    返回SSE流式响应，适合实时显示AI回复
    """
    try:
        if not settings.RAG_ENABLED:
            async def error_stream():
                yield f"data: {ChatResponse(reply='AI助手功能未启用', success=False).json()}\n\n"
            return StreamingResponse(
                error_stream(),
                media_type="text/event-stream"
            )
        
        student_info = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role
        }
        
        rag_client = get_rag_client()
        
        async def generate():
            async for chunk in rag_client.chat_stream(
                message=request.message,
                chat_history=request.chat_history or [],
                student_info=student_info
            ):
                yield f"data: {chunk}\n\n"
        
        logger.info(f"用户 {current_user.username} 开始流式AI对话")
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        logger.error(f"流式AI对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/message", response_model=AssistantMessageResponse)
async def assistant_message(
    request: AssistantMessageRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """AI助手消息接口
    
    兼容前端AIAssistant组件的API调用格式
    """
    try:
        if not settings.RAG_ENABLED:
            return AssistantMessageResponse(
                response="AI助手功能当前未启用。请联系管理员开启RAG系统。",
                success=False
            )
        
        student_info = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role
        }
        
        rag_client = get_rag_client()
        result = await rag_client.chat(
            message=request.question,
            use_rag=True,
            chat_history=[],
            student_info=student_info
        )
        
        logger.info(f"用户 {current_user.username} AI助手消息: {request.question[:50]}...")
        
        suggestions = [
            "省级竞赛加多少分？",
            "社会实践要求多少学时？",
            "如何上传获奖证书？",
            "综测成绩如何计算？"
        ]
        
        return AssistantMessageResponse(
            response=result.get("reply", "抱歉，我现在无法回答。"),
            success=result.get("success", True),
            suggestions=suggestions
        )
    
    except Exception as e:
        logger.error(f"AI助手消息处理失败: {e}", exc_info=True)
        return AssistantMessageResponse(
            response="抱歉，AI助手暂时无法响应。请稍后再试。",
            success=False
        )


@router.get("/suggestions")
async def get_suggestions(
    current_user: TokenData = Depends(get_current_user)
):
    """获取推荐问题列表"""
    return {
        "suggestions": [
            {
                "text": "省级竞赛加多少分？",
                "category": "竞赛加分"
            },
            {
                "text": "社会实践要求多少学时？",
                "category": "社会实践"
            },
            {
                "text": "如何上传获奖证书？",
                "category": "操作指南"
            },
            {
                "text": "综测成绩如何计算？",
                "category": "成绩计算"
            },
            {
                "text": "英语四级可以加多少分？",
                "category": "证书加分"
            },
            {
                "text": "志愿服务时长如何认定？",
                "category": "社会实践"
            }
        ]
    }


@router.get("/history")
async def get_chat_history(
    limit: int = 20,
    current_user: TokenData = Depends(get_current_user)
):
    """获取对话历史
    
    TODO: 实现对话历史持久化存储
    """
    return {
        "history": [],
        "message": "对话历史功能暂未实现"
    }


@router.delete("/history")
async def clear_chat_history(
    current_user: TokenData = Depends(get_current_user)
):
    """清空对话历史"""
    logger.info(f"用户 {current_user.username} 清空对话历史")
    return {"message": "对话历史已清空"}
