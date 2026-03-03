#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中间件模块
包含请求验证、性能监控、日志记录等中间件
"""
import time
import json
import uuid
import logging
import traceback
from typing import Callable, Dict, Any, List, Optional
from datetime import datetime
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logger import get_logger
from app.core.enhanced_logger import (
    APILogMiddleware, sanitize_for_logging, mask_sensitive_data, create_context_logger
)
from app.core.api_response import ResponseCode, ResponseBuilder

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("RequestLogger")
        self.api_logger = APILogMiddleware("APIRequest")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        start_time = time.time()
        
        headers_dict = dict(request.headers)
        query_params = dict(request.query_params)
        
        body_content = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_content = await request.body()
                if body_content:
                    try:
                        body_content = json.loads(body_content.decode('utf-8'))
                    except:
                        body_content = body_content[:500].decode('utf-8', errors='ignore')
            except:
                body_content = None
        
        self.api_logger.log_request(
            method=request.method,
            path=request.url.path,
            headers=headers_dict,
            query_params=query_params,
            body=body_content
        )
        
        self.logger.info(f"[{request_id}] 请求开始: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            elapsed_ms = process_time * 1000
            
            response_summary = None
            if hasattr(response, 'body'):
                try:
                    response_summary = response.body.decode('utf-8')[:200]
                except:
                    pass
            
            self.api_logger.log_response(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                response_summary=response_summary
            )
            
            self.logger.info(
                f"[{request_id}] 请求完成: {response.status_code} "
                f"({process_time*1000:.2f}ms)"
            )
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time*1000:.2f}ms"
            
            return response
            
        except Exception as e:
            error_info = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            
            self.api_logger.log_error(
                method=request.method,
                path=request.url.path,
                error=e,
                extra_info=error_info
            )
            
            self.logger.error(f"[{request_id}] 请求异常: {str(e)}\n{traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "code": ResponseCode.INTERNAL_ERROR,
                    "message": "服务器内部错误",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            )


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    SLOW_REQUEST_THRESHOLD = 1.0  # 慢请求阈值（秒）
    RAG_SLOW_THRESHOLD = 3.0  # RAG请求慢阈值（秒）
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("PerformanceMonitor")
        self.request_stats: Dict[str, Dict] = {}
        self.rag_stats: Dict[str, Dict] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 记录请求统计
        endpoint = f"{request.method} {request.url.path}"
        
        if endpoint not in self.request_stats:
            self.request_stats[endpoint] = {
                "count": 0,
                "total_time": 0,
                "max_time": 0,
                "min_time": float('inf'),
                "error_count": 0
            }
        
        stats = self.request_stats[endpoint]
        stats["count"] += 1
        stats["total_time"] += process_time
        stats["max_time"] = max(stats["max_time"], process_time)
        stats["min_time"] = min(stats["min_time"], process_time)
        
        if response.status_code >= 400:
            stats["error_count"] += 1
        
        # RAG请求特殊监控
        is_rag_request = '/rag/' in request.url.path or '/ai/' in request.url.path or '/chat' in request.url.path
        
        if is_rag_request:
            if endpoint not in self.rag_stats:
                self.rag_stats[endpoint] = {
                    "count": 0,
                    "total_time": 0,
                    "max_time": 0,
                    "min_time": float('inf'),
                    "slow_count": 0
                }
            
            rag_stats = self.rag_stats[endpoint]
            rag_stats["count"] += 1
            rag_stats["total_time"] += process_time
            rag_stats["max_time"] = max(rag_stats["max_time"], process_time)
            rag_stats["min_time"] = min(rag_stats["min_time"], process_time)
            
            if process_time > self.RAG_SLOW_THRESHOLD:
                rag_stats["slow_count"] += 1
                self.logger.warning(
                    f"RAG慢请求警告: {endpoint} 耗时 {process_time*1000:.2f}ms "
                    f"(阈值: {self.RAG_SLOW_THRESHOLD*1000:.0f}ms)"
                )
        
        # 慢请求警告
        if process_time > self.SLOW_REQUEST_THRESHOLD:
            self.logger.warning(
                f"慢请求警告: {endpoint} 耗时 {process_time*1000:.2f}ms"
            )
        
        # 添加性能响应头
        response.headers["X-Response-Time"] = f"{process_time*1000:.2f}ms"
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        result = {}
        for endpoint, stats in self.request_stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            result[endpoint] = {
                "request_count": stats["count"],
                "avg_time_ms": round(avg_time * 1000, 2),
                "max_time_ms": round(stats["max_time"] * 1000, 2),
                "min_time_ms": round(stats["min_time"] * 1000, 2),
                "error_count": stats["error_count"],
                "error_rate": round(stats["error_count"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0
            }
        return result
    
    def get_rag_stats(self) -> Dict[str, Any]:
        """获取RAG性能统计"""
        result = {}
        for endpoint, stats in self.rag_stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            result[endpoint] = {
                "request_count": stats["count"],
                "avg_time_ms": round(avg_time * 1000, 2),
                "max_time_ms": round(stats["max_time"] * 1000, 2),
                "min_time_ms": round(stats["min_time"] * 1000, 2),
                "slow_count": stats["slow_count"],
                "slow_rate": round(stats["slow_count"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0
            }
        return result


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """请求验证中间件"""
    
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_CONTENT_TYPES = [
        "application/json",
        "multipart/form-data",
        "application/x-www-form-urlencoded"
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("RequestValidation")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查Content-Length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=413,
                content={
                    "code": ResponseCode.FILE_SIZE_EXCEEDED,
                    "message": f"请求体大小超过限制 ({self.MAX_CONTENT_LENGTH // 1024 // 1024}MB)",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # 验证Content-Type (仅对有请求体的方法)
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").split(";")[0]
            
            # 对于文件上传，允许multipart/form-data
            if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
                # 如果不是已知类型，但可能是文件上传，放行
                if not content_type.startswith("multipart/"):
                    self.logger.warning(f"未知Content-Type: {content_type}")
        
        return await call_next(request)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """异常处理中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("ExceptionHandler")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            return await call_next(request)
        
        except HTTPException as e:
            self.logger.warning(f"[{request_id}] HTTP异常: {e.status_code} - {e.detail}")
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "code": str(e.status_code),
                    "message": str(e.detail),
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except ValueError as e:
            self.logger.error(f"[{request_id}] 参数错误: {str(e)}")
            
            return JSONResponse(
                status_code=400,
                content={
                    "code": ResponseCode.VALIDATION_ERROR,
                    "message": f"参数验证失败: {str(e)}",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except Exception as e:
            self.logger.error(f"[{request_id}] 未处理异常: {str(e)}", exc_info=True)
            
            return JSONResponse(
                status_code=500,
                content={
                    "code": ResponseCode.INTERNAL_ERROR,
                    "message": "服务器内部错误",
                    "detail": str(e) if settings.DEBUG else None,
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            )


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件"""
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = True
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)
        
        # 添加CORS头
        origin = request.headers.get("origin", "*")
        
        if "*" in self.allow_origins or origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin if origin != "*" else "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """请求限流中间件"""
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        super().__init__(app)
        self.logger = get_logger("RateLimit")
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_history: Dict[str, List[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端标识
        client_ip = request.client.host if request.client else "unknown"
        client_id = f"{client_ip}:{request.url.path}"
        
        current_time = time.time()
        
        # 清理过期记录
        if client_id in self.request_history:
            self.request_history[client_id] = [
                t for t in self.request_history[client_id]
                if current_time - t < 3600  # 保留1小时内的记录
            ]
        else:
            self.request_history[client_id] = []
        
        # 检查分钟限制
        minute_requests = [
            t for t in self.request_history[client_id]
            if current_time - t < 60
        ]
        
        if len(minute_requests) >= self.requests_per_minute:
            self.logger.warning(f"请求限流: {client_id} 超过每分钟限制")
            return JSONResponse(
                status_code=429,
                content={
                    "code": ResponseCode.TOO_MANY_REQUESTS,
                    "message": "请求过于频繁，请稍后再试",
                    "timestamp": datetime.now().isoformat()
                },
                headers={"Retry-After": "60"}
            )
        
        # 检查小时限制
        if len(self.request_history[client_id]) >= self.requests_per_hour:
            self.logger.warning(f"请求限流: {client_id} 超过每小时限制")
            return JSONResponse(
                status_code=429,
                content={
                    "code": ResponseCode.TOO_MANY_REQUESTS,
                    "message": "请求次数超过限制，请稍后再试",
                    "timestamp": datetime.now().isoformat()
                },
                headers={"Retry-After": "3600"}
            )
        
        # 记录请求
        self.request_history[client_id].append(current_time)
        
        return await call_next(request)


# 导入settings（延迟导入避免循环依赖）
from config import settings
