#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用工厂模块

负责创建和配置FastAPI应用实例。
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from app.core.logger import logger
from app.core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.core.db_connection import get_db_connection_manager
from app.core.executor_manager import executor_manager
from app.api import api_router
from config import settings
from app.services.ocr_service import get_ocr_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("应用启动中...")
    
    # 初始化数据库连接
    db_manager = get_db_connection_manager()
    await db_manager.init_connection()
    
    # 初始化线程池执行器
    executor_manager.get_executor()
    
    # 预热OCR引擎以提升首个请求的响应速度
    try:
        get_ocr_service().warm_up()
    except Exception:
        # 预热失败不会阻塞应用启动
        logger.warning("OCR引擎预热失败，将在首次请求时初始化", exc_info=True)
    
    logger.info("应用启动完成")
    
    yield
    
    logger.info("应用关闭中...")
    
    # 关闭线程池执行器
    await executor_manager.aclose()
    
    # 关闭数据库连接
    await db_manager.close_connection()
    
    logger.info("应用关闭完成")


def setup_middleware(app: FastAPI):
    """配置中间件"""
    # CORS中间件 - 允许前端和RAG系统跨域访问
    # 注意：allow_credentials=True 时不能使用 allow_origins=["*"]
    allowed_origins = [
        "http://localhost:5173",      # 前端开发服务器
        "http://localhost:8080",      # 前端生产服务器
        "http://localhost:8000",      # RAG系统
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"]
    )
    
    # 请求处理中间件
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        start_time = time.time()
        logger.info(f"请求: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"响应: {response.status_code} - {process_time:.4f}s")
        
        return response


def register_exception_handlers(app: FastAPI):
    """注册异常处理器"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan
    )
    
    # 配置中间件
    setup_middleware(app)
    
    # 注册异常处理器
    register_exception_handlers(app)
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app
