#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块 - 兼容层
实际实现请参考 enhanced_logger.py
"""
from app.core.enhanced_logger import (
    logger,
    get_logger,
    setup_logger,
    set_request_id,
    get_request_id,
    set_user_id,
    get_user_id,
    set_operation,
    get_operation,
    clear_context,
    get_log_context,
    RequestContext,
    log_function_call,
    log_async_function_call,
    log_business_event,
    log_data_flow,
    log_branch_decision,
    LogLevel,
    LogContext,
    mask_sensitive_data,
    sanitize_for_logging,
    create_context_logger,
    APILogMiddleware,
    setup_logging,
)

__all__ = [
    'logger',
    'get_logger',
    'setup_logger',
    'set_request_id',
    'get_request_id',
    'set_user_id',
    'get_user_id',
    'set_operation',
    'get_operation',
    'clear_context',
    'get_log_context',
    'RequestContext',
    'log_function_call',
    'log_async_function_call',
    'log_business_event',
    'log_data_flow',
    'log_branch_decision',
    'LogLevel',
    'LogContext',
    'mask_sensitive_data',
    'sanitize_for_logging',
    'create_context_logger',
    'APILogMiddleware',
    'setup_logging',
]
