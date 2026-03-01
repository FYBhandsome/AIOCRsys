#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API数据追踪模块
在API访问的业务逻辑关键节点插入详细的数据打印语句
"""
import json
import time
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime

from app.core.logger import get_logger, set_request_id, get_request_id, set_user_id, get_user_id

logger = get_logger(__name__)


def trace_api_call(
    operation_name: str = None,
    log_request: bool = True,
    log_response: bool = True,
    log_time: bool = True,
    sensitive_fields: list = None
):
    """API调用追踪装饰器
    
    在API访问的业务逻辑关键节点插入详细的数据打印语句
    
    Args:
        operation_name: 操作名称
        log_request: 是否记录请求参数
        log_response: 是否记录响应结果
        log_time: 是否记录执行时间
        sensitive_fields: 敏感字段列表（将被遮蔽）
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'secret', 'key', 'credential']
    
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            trace_id = get_request_id() or f"trace_{int(time.time()*1000)}"
            start_time = time.time()
            
            print(f"\n{'='*60}")
            print(f"[API追踪] {op_name}")
            print(f"{'='*60}")
            print(f"追踪ID: {trace_id}")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            print(f"用户ID: {get_user_id() or '未认证'}")
            
            if log_request:
                print(f"\n[请求参数]")
                print(f"  函数: {func.__name__}")
                if args:
                    print(f"  位置参数: {_safe_repr(args, sensitive_fields)}")
                if kwargs:
                    print(f"  关键字参数: {_safe_repr(kwargs, sensitive_fields)}")
            
            try:
                result = await func(*args, **kwargs)
                
                if log_response:
                    print(f"\n[响应结果]")
                    print(f"  状态: 成功")
                    print(f"  数据: {_safe_repr(result, sensitive_fields, max_length=500)}")
                
                if log_time:
                    elapsed_ms = (time.time() - start_time) * 1000
                    print(f"\n[执行时间] {elapsed_ms:.2f}ms")
                
                print(f"{'='*60}\n")
                
                logger.info(f"[{trace_id}] {op_name} 执行成功 ({elapsed_ms:.2f}ms)")
                return result
                
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                
                print(f"\n[响应结果]")
                print(f"  状态: 失败")
                print(f"  异常类型: {type(e).__name__}")
                print(f"  异常信息: {str(e)}")
                print(f"\n[执行时间] {elapsed_ms:.2f}ms")
                print(f"{'='*60}\n")
                
                logger.error(f"[{trace_id}] {op_name} 执行失败: {type(e).__name__}: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            trace_id = get_request_id() or f"trace_{int(time.time()*1000)}"
            start_time = time.time()
            
            print(f"\n{'='*60}")
            print(f"[API追踪] {op_name}")
            print(f"{'='*60}")
            print(f"追踪ID: {trace_id}")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            print(f"用户ID: {get_user_id() or '未认证'}")
            
            if log_request:
                print(f"\n[请求参数]")
                print(f"  函数: {func.__name__}")
                if args:
                    print(f"  位置参数: {_safe_repr(args, sensitive_fields)}")
                if kwargs:
                    print(f"  关键字参数: {_safe_repr(kwargs, sensitive_fields)}")
            
            try:
                result = func(*args, **kwargs)
                
                if log_response:
                    print(f"\n[响应结果]")
                    print(f"  状态: 成功")
                    print(f"  数据: {_safe_repr(result, sensitive_fields, max_length=500)}")
                
                if log_time:
                    elapsed_ms = (time.time() - start_time) * 1000
                    print(f"\n[执行时间] {elapsed_ms:.2f}ms")
                
                print(f"{'='*60}\n")
                
                logger.info(f"[{trace_id}] {op_name} 执行成功 ({elapsed_ms:.2f}ms)")
                return result
                
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                
                print(f"\n[响应结果]")
                print(f"  状态: 失败")
                print(f"  异常类型: {type(e).__name__}")
                print(f"  异常信息: {str(e)}")
                print(f"\n[执行时间] {elapsed_ms:.2f}ms")
                print(f"{'='*60}\n")
                
                logger.error(f"[{trace_id}] {op_name} 执行失败: {type(e).__name__}: {e}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def trace_data_flow(step_name: str, data: Any, extra_info: Dict = None):
    """数据流追踪打印
    
    在数据处理过程中打印中间数据
    
    Args:
        step_name: 步骤名称
        data: 数据内容
        extra_info: 额外信息
    """
    print(f"\n[数据流] {step_name}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"  数据类型: {type(data).__name__}")
    
    if isinstance(data, dict):
        print(f"  字段: {list(data.keys())}")
        print(f"  内容: {_safe_repr(data, max_length=300)}")
    elif isinstance(data, (list, tuple)):
        print(f"  长度: {len(data)}")
        if len(data) > 0:
            print(f"  首项: {_safe_repr(data[0], max_length=100)}")
    else:
        print(f"  内容: {_safe_repr(data, max_length=300)}")
    
    if extra_info:
        print(f"  额外信息: {_safe_repr(extra_info, max_length=200)}")
    
    logger.debug(f"[数据流] {step_name} | 类型: {type(data).__name__}")


def trace_database_query(
    query_type: str,
    table: str,
    conditions: Dict = None,
    result_count: int = None,
    elapsed_ms: float = None
):
    """数据库查询追踪
    
    Args:
        query_type: 查询类型 (SELECT, INSERT, UPDATE, DELETE)
        table: 表名
        conditions: 查询条件
        result_count: 结果数量
        elapsed_ms: 执行时间
    """
    print(f"\n[数据库查询]")
    print(f"  类型: {query_type}")
    print(f"  表: {table}")
    
    if conditions:
        print(f"  条件: {_safe_repr(conditions, max_length=200)}")
    
    if result_count is not None:
        print(f"  结果数量: {result_count}")
    
    if elapsed_ms is not None:
        print(f"  执行时间: {elapsed_ms:.2f}ms")
    
    logger.debug(f"[DB] {query_type} {table} | 条件: {conditions} | 结果: {result_count}")


def trace_external_api(
    api_name: str,
    endpoint: str,
    method: str = "GET",
    request_data: Any = None,
    response_data: Any = None,
    status_code: int = None,
    elapsed_ms: float = None
):
    """外部API调用追踪
    
    Args:
        api_name: API名称
        endpoint: 端点
        method: HTTP方法
        request_data: 请求数据
        response_data: 响应数据
        status_code: 状态码
        elapsed_ms: 执行时间
    """
    print(f"\n[外部API调用] {api_name}")
    print(f"  端点: {endpoint}")
    print(f"  方法: {method}")
    
    if request_data:
        print(f"  请求数据: {_safe_repr(request_data, max_length=200)}")
    
    if status_code:
        print(f"  状态码: {status_code}")
    
    if response_data:
        print(f"  响应数据: {_safe_repr(response_data, max_length=200)}")
    
    if elapsed_ms:
        print(f"  执行时间: {elapsed_ms:.2f}ms")
    
    logger.info(f"[外部API] {method} {endpoint} -> {status_code} ({elapsed_ms:.2f}ms)")


def trace_business_logic(
    operation: str,
    input_data: Any = None,
    output_data: Any = None,
    decision: str = None,
    reason: str = None
):
    """业务逻辑追踪
    
    Args:
        operation: 操作名称
        input_data: 输入数据
        output_data: 输出数据
        decision: 决策结果
        reason: 决策原因
    """
    print(f"\n[业务逻辑] {operation}")
    
    if input_data:
        print(f"  输入: {_safe_repr(input_data, max_length=200)}")
    
    if decision:
        print(f"  决策: {decision}")
    
    if reason:
        print(f"  原因: {reason}")
    
    if output_data:
        print(f"  输出: {_safe_repr(output_data, max_length=200)}")
    
    logger.debug(f"[业务] {operation} | 决策: {decision}")


def _safe_repr(data: Any, sensitive_fields: list = None, max_length: int = 1000) -> str:
    """安全的数据表示
    
    遮蔽敏感字段并限制长度
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'secret', 'key', 'credential']
    
    try:
        if isinstance(data, dict):
            safe_data = {}
            for k, v in data.items():
                if any(s in k.lower() for s in sensitive_fields):
                    safe_data[k] = "***REDACTED***"
                elif isinstance(v, (dict, list)):
                    safe_data[k] = _safe_repr(v, sensitive_fields, max_length=200)
                else:
                    safe_data[k] = v
            data = safe_data
        elif isinstance(data, (list, tuple)):
            data = [_safe_repr(item, sensitive_fields, max_length=200) if isinstance(item, (dict, list)) else item for item in data]
        
        json_str = json.dumps(data, ensure_ascii=False, default=str)
        
        if len(json_str) > max_length:
            return json_str[:max_length] + "..."
        return json_str
    except Exception as e:
        return f"<无法序列化: {type(data).__name__}: {e}>"


class DataTracer:
    """数据追踪器上下文管理器"""
    
    def __init__(self, operation_name: str, **context):
        self.operation_name = operation_name
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        print(f"\n{'='*60}")
        print(f"[追踪开始] {self.operation_name}")
        print(f"{'='*60}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        for k, v in self.context.items():
            print(f"{k}: {_safe_repr(v, max_length=200)}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self.start_time) * 1000
        
        if exc_type:
            print(f"\n[追踪结束] {self.operation_name} - 失败")
            print(f"异常: {exc_type.__name__}: {exc_val}")
        else:
            print(f"\n[追踪结束] {self.operation_name} - 成功")
        
        print(f"总耗时: {elapsed_ms:.2f}ms")
        print(f"{'='*60}\n")
        
        return False
    
    def log_step(self, step_name: str, data: Any = None):
        """记录步骤"""
        print(f"  [{step_name}] {_safe_repr(data, max_length=200) if data else ''}")
    
    def log_decision(self, decision: str, reason: str = None):
        """记录决策"""
        print(f"  [决策] {decision}")
        if reason:
            print(f"  [原因] {reason}")
