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


class APIRouteBuilder:
    """API路由构建器"""
    
    def __init__(self, prefix: str = "", tags: List[str] = None):
        self.router = APIRouter(prefix=prefix)
        self.tags = tags or []
    
    def get(
        self,
        path: str,
        summary: str = "",
        description: str = "",
        response_model: type = None
    ):
        """注册GET端点"""
        return self._register_endpoint(
            "GET", path, summary, description, response_model
        )
    
    def post(
        self,
        path: str,
        summary: str = "",
        description: str = "",
        response_model: type = None
    ):
        """注册POST端点"""
        return self._register_endpoint(
            "POST", path, summary, description, response_model
        )
    
    def put(
        self,
        path: str,
        summary: str = "",
        description: str = "",
        response_model: type = None
    ):
        """注册PUT端点"""
        return self._register_endpoint(
            "PUT", path, summary, description, response_model
        )
    
    def delete(
        self,
        path: str,
        summary: str = "",
        description: str = "",
        response_model: type = None
    ):
        """注册DELETE端点"""
        return self._register_endpoint(
            "DELETE", path, summary, description, response_model
        )
    
    def patch(
        self,
        path: str,
        summary: str = "",
        description: str = "",
        response_model: type = None
    ):
        """注册PATCH端点"""
        return self._register_endpoint(
            "PATCH", path, summary, description, response_model
        )
    
    def _register_endpoint(
        self,
        method: str,
        path: str,
        summary: str,
        description: str,
        response_model: type
    ):
        """注册端点"""
        endpoint = APIEndpoint(
            path=self.router.prefix + path,
            method=method,
            summary=summary,
            description=description,
            tags=self.tags,
            response_model=response_model
        )
        api_registry.register_endpoint(endpoint)
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except ApiException as e:
                    raise HTTPException(
                        status_code=e.http_status,
                        detail={"code": e.code, "message": e.message, "errors": e.errors}
                    )
                except Exception as e:
                    logger.error(f"API处理异常: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={"code": ResponseCode.INTERNAL_ERROR, "message": str(e)}
                    )
            
            route_method = getattr(self.router, method.lower())
            return route_method(
                path,
                summary=summary,
                description=description,
                tags=self.tags,
                response_model=response_model
            )(wrapper)
        
        return decorator
    
    def build(self) -> APIRouter:
        """构建路由器"""
        return self.router


def api_handler(func):
    """
    API处理装饰器
    自动处理异常并返回统一格式响应
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request_id = None
        try:
            if args and hasattr(args[0], 'state'):
                request_id = getattr(args[0].state, 'request_id', None)
            
            result = await func(*args, **kwargs)
            
            if isinstance(result, dict):
                if "code" in result:
                    return result
                return ResponseBuilder.success(data=result, request_id=request_id)
            elif isinstance(result, ApiResponse):
                return result.model_dump()
            elif result is None:
                return ResponseBuilder.success(request_id=request_id)
            else:
                return ResponseBuilder.success(data=result, request_id=request_id)
                
        except ApiException as e:
            logger.warning(f"API异常: {e.code} - {e.message}")
            return ResponseBuilder.error(
                message=e.message,
                code=e.code,
                errors=e.errors,
                request_id=request_id
            )
        except HTTPException as e:
            logger.warning(f"HTTP异常: {e.status_code} - {e.detail}")
            return ResponseBuilder.error(
                message=str(e.detail),
                code=str(e.status_code),
                request_id=request_id
            )
        except ValueError as e:
            logger.warning(f"参数错误: {e}")
            return ResponseBuilder.error(
                message=f"参数错误: {str(e)}",
                code=ResponseCode.VALIDATION_ERROR,
                request_id=request_id
            )
        except Exception as e:
            logger.error(f"未处理异常: {e}", exc_info=True)
            return ResponseBuilder.error(
                message="服务器内部错误",
                code=ResponseCode.INTERNAL_ERROR,
                request_id=request_id
            )
    
    return wrapper


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


def get_service_dependency(service_name: str):
    """获取服务依赖"""
    return container.get_dependency(service_name)


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
