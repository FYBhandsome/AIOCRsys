#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一API入口管理模块
提供API路由注册、依赖注入、请求处理等功能
"""
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
import inspect
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.api_response import (
    ApiResponse, ResponseBuilder, ResponseCode, ApiException,
    BadRequestException, UnauthorizedException, ForbiddenException,
    NotFoundException, ValidationException, PagedResponse
)
from app.core.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class APIEndpoint:
    """API端点描述类"""
    
    def __init__(
        self,
        path: str,
        method: str,
        summary: str = "",
        description: str = "",
        tags: List[str] = None,
        response_model: type = None,
        dependencies: List = None
    ):
        self.path = path
        self.method = method.upper()
        self.summary = summary
        self.description = description
        self.tags = tags or []
        self.response_model = response_model
        self.dependencies = dependencies or []


class APIRegistry:
    """API注册中心"""
    
    _instance = None
    _endpoints: Dict[str, APIEndpoint] = {}
    _routers: Dict[str, APIRouter] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_endpoint(self, endpoint: APIEndpoint):
        """注册API端点"""
        key = f"{endpoint.method}:{endpoint.path}"
        self._endpoints[key] = endpoint
        logger.debug(f"注册API端点: {key}")
    
    def register_router(self, name: str, router: APIRouter):
        """注册路由器"""
        self._routers[name] = router
        logger.info(f"注册路由器: {name}")
    
    def get_endpoint(self, path: str, method: str) -> Optional[APIEndpoint]:
        """获取API端点"""
        key = f"{method.upper()}:{path}"
        return self._endpoints.get(key)
    
    def get_all_endpoints(self) -> List[APIEndpoint]:
        """获取所有API端点"""
        return list(self._endpoints.values())
    
    def get_router(self, name: str) -> Optional[APIRouter]:
        """获取路由器"""
        return self._routers.get(name)


api_registry = APIRegistry()


def paged_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """构建分页响应"""
    return ResponseBuilder.paged(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


def validate_request(model: BaseModel):
    """
    请求验证装饰器
    验证请求数据是否符合指定的Pydantic模型
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for arg in args:
                if isinstance(arg, model):
                    break
            else:
                for key, value in kwargs.items():
                    if isinstance(value, model):
                        break
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class DependencyContainer:
    """依赖注入容器"""
    
    _instance = None
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Callable] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, name: str, service: Any):
        """注册服务实例"""
        self._services[name] = service
        logger.debug(f"注册服务: {name}")
    
    def register_factory(self, name: str, factory: Callable):
        """注册服务工厂"""
        self._factories[name] = factory
        logger.debug(f"注册服务工厂: {name}")
    
    def get(self, name: str) -> Any:
        """获取服务"""
        if name in self._services:
            return self._services[name]
        
        if name in self._factories:
            service = self._factories[name]()
            self._services[name] = service
            return service
        
        raise ValueError(f"服务未注册: {name}")
    
    def get_dependency(self, name: str):
        """获取依赖注入函数"""
        def dependency():
            return self.get(name)
        return Depends(dependency)


container = DependencyContainer()



class RequestContext:
    """请求上下文"""
    
    def __init__(self, request: Request):
        self.request = request
        self._data: Dict[str, Any] = {}
    
    @property
    def request_id(self) -> str:
        return getattr(self.request.state, 'request_id', 'unknown')
    
    @property
    def client_ip(self) -> str:
        return self.request.client.host if self.request.client else "unknown"
    
    @property
    def user_agent(self) -> str:
        return self.request.headers.get("user-agent", "")
    
    @property
    def user_id(self) -> Optional[str]:
        return getattr(self.request.state, 'user_id', None)
    
    @property
    def user_role(self) -> Optional[str]:
        return getattr(self.request.state, 'user_role', None)
    
    def set(self, key: str, value: Any):
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


def get_request_context(request: Request) -> RequestContext:
    """获取请求上下文依赖"""
    return RequestContext(request)


class APIVersion:
    """API版本管理"""
    
    V1 = "/api/v1"
    V2 = "/api/v2"
    
    @staticmethod
    def get_version_prefix(version: str) -> str:
        """获取版本前缀"""
        versions = {
            "v1": APIVersion.V1,
            "v2": APIVersion.V2
        }
        return versions.get(version.lower(), APIVersion.V1)


def create_api_response(
    data: Any = None,
    message: str = "操作成功",
    code: str = ResponseCode.SUCCESS,
    errors: List[Dict] = None
) -> Dict[str, Any]:
    """创建API响应"""
    if errors:
        return ResponseBuilder.error(message, code, errors)
    return ResponseBuilder.success(data, message)


def create_error_response(
    message: str,
    code: str = ResponseCode.INTERNAL_ERROR,
    errors: List[Dict] = None
) -> Dict[str, Any]:
    """创建错误响应"""
    return ResponseBuilder.error(message, code, errors)
