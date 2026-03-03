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
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException
from contextlib import asynccontextmanager
import time
from typing import Dict, Any
from pathlib import Path

from app.core.logger import logger, setup_logging, get_logger
from app.core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    business_exception_handler,
    BusinessError
)
from app.core.db_connection import get_db_connection_manager
from app.core.executor_manager import executor_manager
from app.core.middleware import (
    RequestLoggingMiddleware,
    PerformanceMonitorMiddleware,
    RequestValidationMiddleware,
    RateLimitMiddleware
)
from app.core.api_response import ResponseCode
from app.api import api_router
from config import settings
from app.services.ocr_service import get_ocr_service


def init_logging():
    """初始化增强版日志系统"""
    from config import UNIFIED_LOG_DIR
    UNIFIED_LOG_DIR.mkdir(parents=True, exist_ok=True)
    setup_logging(
        log_dir=str(UNIFIED_LOG_DIR),
        service_name="visual_model",
        console_level=20,
        file_level=10
    )
    return get_logger("app")


init_logging()
app_logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    app_logger.info("应用启动中...")
    
    db_manager = get_db_connection_manager()
    await db_manager.init_connection()
    app_logger.info("数据库连接初始化完成")
    
    executor_manager.get_executor()
    app_logger.info("线程池执行器初始化完成")
    
    try:
        get_ocr_service().warm_up()
        app_logger.info("OCR引擎预热完成")
    except Exception as e:
        app_logger.warning(f"OCR引擎预热失败: {e}", exc_info=True)
    
    app_logger.info("应用启动完成")
    
    yield
    
    app_logger.info("应用关闭中...")
    
    await executor_manager.aclose()
    app_logger.info("线程池执行器已关闭")
    
    await db_manager.close_connection()
    app_logger.info("数据库连接已关闭")
    
    app_logger.info("应用关闭完成")


def setup_middleware(app: FastAPI):
    """配置中间件"""
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://localhost:8010",
        "http://localhost:8011",
        "http://localhost:8012",
        "http://localhost:8013",
        "http://localhost:8014",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003",
        "http://127.0.0.1:8004",
        "http://127.0.0.1:8005",
        "http://127.0.0.1:8006",
        "http://127.0.0.1:8010",
        "http://127.0.0.1:8011",
        "http://127.0.0.1:8012",
        "http://127.0.0.1:8013",
        "http://127.0.0.1:8014",
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-Request-ID", "X-Response-Time"]
    )
    
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(PerformanceMonitorMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    
    if settings.RATE_LIMIT_CALLS > 0:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.RATE_LIMIT_CALLS,
            requests_per_hour=settings.RATE_LIMIT_CALLS * 10
        )
    
    logger.info("中间件配置完成")


def register_exception_handlers(app: FastAPI):
    """注册异常处理器"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(BusinessError, business_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"全局异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": ResponseCode.INTERNAL_ERROR,
                "message": "服务器内部错误",
                "detail": str(exc) if settings.DEBUG else None
            }
        )


def custom_openapi(app: FastAPI):
    """自定义OpenAPI文档"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=f"""
{settings.PROJECT_DESCRIPTION}

## API接口文档

### 认证说明
- 大部分API需要通过Bearer Token进行认证
- 登录接口返回的token需要在请求头中携带: `Authorization: Bearer <token>`

### 响应格式
所有API响应遵循统一格式：
```json
{{
  "code": "200",
  "message": "操作成功",
  "data": {{}},
  "timestamp": "2024-01-01T12:00:00",
  "request_id": "req_123456"
}}
```

### 错误码说明
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 业务模块
- **认证模块**: 用户登录、注册、权限管理
- **学生模块**: 学生信息管理、成绩查询、材料上传
- **教师模块**: 班级管理、学生列表、成绩分析
- **管理员模块**: 用户管理、系统设置、规则管理
- **综测模块**: 综合测评计算、成绩导入导出
- **证书模块**: 证书上传、OCR识别、审核管理
- **文件模块**: 文件上传下载、分片上传管理
- **RAG模块**: 规则检索、智能填充、AI对话

### 新增接口 (v2.4.0)
- `POST /v1/student/material/upload` - 学生材料上传
- `GET /v1/student/materials` - 获取学生材料列表
- `GET /api/stats` - 获取系统性能统计（含RAG性能）
- `GET /health` - 健康检查端点

### 性能监控
系统提供以下性能监控功能：
- 请求响应时间监控（X-Response-Time响应头）
- 慢请求警告（>1秒）
- RAG请求特殊监控（>3秒警告）
- 请求统计（次数、平均时间、错误率）
""",
        routes=app.routes,
        tags=[
            {"name": "认证", "description": "用户认证相关接口 - 登录、注册、权限验证"},
            {"name": "学生", "description": "学生信息管理接口 - 成绩查询、材料上传、综测查看"},
            {"name": "教师", "description": "教师信息管理接口 - 班级管理、学生列表、成绩分析"},
            {"name": "管理员", "description": "管理员操作接口 - 用户管理、系统配置、规则管理"},
            {"name": "综测", "description": "综合测评相关接口 - 配置管理、成绩计算、排名查询"},
            {"name": "证书", "description": "证书管理相关接口 - 上传、OCR识别、审核"},
            {"name": "文件", "description": "文件上传下载接口 - 分片上传、文件管理"},
            {"name": "OCR", "description": "OCR识别相关接口 - 图片识别、批量处理"},
            {"name": "RAG", "description": "RAG检索相关接口 - 规则检索、智能填充、AI对话"},
            {"name": "系统", "description": "系统管理接口 - 健康检查、性能统计"},
        ]
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    app.openapi = lambda: custom_openapi(app)
    
    setup_middleware(app)
    
    register_exception_handlers(app)
    
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    @app.get("/health", tags=["系统"])
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "version": settings.PROJECT_VERSION,
            "debug": settings.DEBUG
        }
    
    @app.get("/api/v1/health", tags=["系统"])
    async def api_health_check():
        """API健康检查端点（前端兼容）"""
        return {
            "status": "healthy",
            "service": "Visual Model Backend",
            "version": settings.PROJECT_VERSION,
            "debug": settings.DEBUG
        }
    
    @app.get("/api/stats", tags=["系统"])
    async def get_stats():
        """获取系统统计信息"""
        from app.core.middleware import PerformanceMonitorMiddleware
        
        for middleware in app.user_middleware:
            if isinstance(middleware, PerformanceMonitorMiddleware):
                return {
                    "performance": middleware.get_stats(),
                    "rag_performance": middleware.get_rag_stats()
                }
        
        return {"performance": {}, "rag_performance": {}}
    
    logger.info(f"应用创建完成: {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    
    return app
