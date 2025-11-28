"""
聊天相关API路由
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.models import ChatRequest, ApiResponse
from app.core.dependencies import DependencyContainer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI对话"])

# 创建依赖注入容器实例
container = DependencyContainer()


@router.post("")
async def chat(request: ChatRequest):
    """处理用户聊天请求"""
    try:
        chat_service = container.get_chat_service()
        
        result = chat_service.chat(
            question=request.message,
            history=request.chat_history,
            use_cache=True,
            use_optimized=False
        )
        
        return ApiResponse(
            success=True,
            data=result,
            message="对话处理成功"
        )
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """处理用户聊天请求 - 流式响应"""
    try:
        chat_service = container.get_chat_service()
        
        return StreamingResponse(
            chat_service.chat_stream(
                question=request.message,
                history=request.chat_history
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    except Exception as e:
        logger.error(f"流式对话处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"流式对话处理失败: {str(e)}")
