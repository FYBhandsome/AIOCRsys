"""
Visual Model服务日志配置模块 - 兼容层
====================================

此模块作为兼容层，所有日志功能由 app.core.enhanced_logger 提供。
保留此文件是为了向后兼容现有代码的导入语句。

使用方法:
    from app.core.logger import get_logger, setup_logging
    
    setup_logging(service_name="visual_model")
    logger = get_logger(__name__)
"""

from app.core.enhanced_logger import (
    logger,
    get_logger,
    setup_logger,
    setup_logging,
    set_request_id,
    get_request_id,
    set_user_id,
    get_user_id,
    set_session_id,
    get_session_id,
    set_operation,
    get_operation,
    clear_context,
    get_log_context,
    mask_sensitive_data,
    mask_dict,
    LogContext,
    log_function_call,
    log_async_function_call,
    log_business_event,
    log_data_flow,
    log_branch_decision,
    LogLevel,
    RequestContext,
    sanitize_for_logging,
    create_context_logger,
    APILogMiddleware,
    UNIFIED_LOG_DIR,
    cleanup_old_logs,
    cleanup_root_log_files,
    get_service_log_dir,
)

__all__ = [
    'logger',
    'get_logger',
    'setup_logger',
    'setup_logging',
    'set_request_id',
    'get_request_id',
    'set_user_id',
    'get_user_id',
    'set_session_id',
    'get_session_id',
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
    'mask_dict',
    'sanitize_for_logging',
    'create_context_logger',
    'APILogMiddleware',
    'UNIFIED_LOG_DIR',
    'cleanup_old_logs',
    'cleanup_root_log_files',
    'get_service_log_dir',
]
