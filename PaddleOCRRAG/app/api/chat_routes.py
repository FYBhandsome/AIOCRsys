"""
聊天相关API路由 - 使用统一响应格式
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.models import ChatRequest
from app.core.dependencies import DependencyContainer
from app.core.logger import get_logger, set_request_id, RequestContext, performance_monitor
from app.core.api_response import ResponseBuilder, ResponseCode

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["AI对话"])

container = DependencyContainer()


@router.post("")
async def chat(request: ChatRequest):
    """处理用户聊天请求"""
    request_id = set_request_id()
    
    with RequestContext(request_id=request_id):
        logger.info(
            f"收到聊天请求",
            extra={'params': {'message': request.message[:50] if request.message else '', 'use_rag': request.use_rag}}
        )
        
        try:
            chat_service = container.get_chat_service()
            
            history = []
            if request.chat_history:
                for msg in request.chat_history:
                    if hasattr(msg, 'dict'):
                        history.append(msg.dict())
                    elif hasattr(msg, 'content'):
                        history.append({"role": msg.role, "content": msg.content})
                    elif isinstance(msg, dict):
                        history.append(msg)
                    else:
                        logger.warning(f"未知的消息格式: {type(msg)}")
            
            logger.debug(f"处理后的对话历史长度: {len(history)}")
            
            result = chat_service.chat(
                question=request.message,
                history=history,
                use_cache=True,
                use_optimized=False,
                use_rag=request.use_rag
            )
            
            logger.info(
                f"聊天请求处理成功",
                extra={'params': {'request_id': request_id, 'used_rag': result.get('used_rag', False)}}
            )
            
            return ResponseBuilder.success(
                data=result,
                message="对话处理成功",
                request_id=request_id
            )
        except Exception as e:
            logger.error(f"对话处理失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """处理用户聊天请求 - 流式响应"""
    request_id = set_request_id()
    
    with RequestContext(request_id=request_id):
        logger.info(
            f"收到流式聊天请求",
            extra={'params': {'message': request.message[:50] if request.message else '', 'use_rag': request.use_rag}}
        )
        
        try:
            chat_service = container.get_chat_service()
            
            return StreamingResponse(
                chat_service.chat_stream(
                    question=request.message,
                    history=request.chat_history,
                    use_rag=request.use_rag
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "X-Request-ID": request_id
                }
            )
        except Exception as e:
            logger.error(f"流式对话处理失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"流式对话处理失败: {str(e)}")


@router.post("/async")
async def chat_async(request: ChatRequest):
    """处理用户聊天请求 - 异步模式"""
    request_id = set_request_id()
    
    with RequestContext(request_id=request_id):
        logger.info(
            f"收到异步聊天请求",
            extra={'params': {'message': request.message[:50] if request.message else '', 'use_rag': request.use_rag}}
        )
        
        try:
            chat_service = container.get_chat_service()
            
            result = await chat_service.chat_async(
                question=request.message,
                history=request.chat_history,
                use_cache=True,
                use_rag=request.use_rag
            )
            
            logger.info(f"异步聊天请求处理成功")
            
            return ResponseBuilder.success(
                data=result,
                message="异步对话处理成功",
                request_id=request_id
            )
        except Exception as e:
            logger.error(f"异步对话处理失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"异步对话处理失败: {str(e)}")


@router.post("/stream/async")
async def chat_stream_async(request: ChatRequest):
    """处理用户聊天请求 - 异步流式响应"""
    request_id = set_request_id()
    
    with RequestContext(request_id=request_id):
        logger.info(
            f"收到异步流式聊天请求",
            extra={'params': {'message': request.message[:50] if request.message else '', 'use_rag': request.use_rag}}
        )
        
        try:
            chat_service = container.get_chat_service()
            
            async def generate():
                async for chunk in chat_service.chat_stream_async(
                    question=request.message,
                    history=request.chat_history,
                    use_rag=request.use_rag
                ):
                    yield chunk
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "X-Request-ID": request_id
                }
            )
        except Exception as e:
            logger.error(f"异步流式对话处理失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"异步流式对话处理失败: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats():
    """获取聊天缓存统计"""
    logger.debug("获取聊天缓存统计")
    try:
        chat_service = container.get_chat_service()
        stats = chat_service.get_cache_stats()
        
        return ResponseBuilder.success(
            data=stats,
            message="获取缓存统计成功"
        )
    except Exception as e:
        logger.error(f"获取缓存统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.delete("/cache")
async def clear_cache():
    """清空聊天缓存"""
    logger.info("清空聊天缓存")
    try:
        chat_service = container.get_chat_service()
        chat_service.clear_cache()
        
        return ResponseBuilder.success(
            data={"cleared_at": datetime.now().isoformat()},
            message="缓存已清空"
        )
    except Exception as e:
        logger.error(f"清空缓存失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空缓存失败: {str(e)}")
