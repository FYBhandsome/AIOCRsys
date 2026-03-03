"""
RAG服务日志配置模块 - 兼容层
============================

此模块作为兼容层，所有日志功能由 shared_utils.unified_logger 提供。
保留此文件是为了向后兼容现有代码的导入语句。

使用方法:
    from app.core.logger import get_logger, setup_logging
    
    setup_logging(service_name="rag")
    logger = get_logger(__name__)
"""

import sys
import time
import threading
from pathlib import Path
from functools import wraps
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared_utils.unified_logger import (
    setup_logging,
    get_logger,
    set_request_id,
    get_request_id,
    set_user_id,
    get_user_id,
    set_session_id,
    get_session_id,
    set_operation,
    get_operation,
    clear_context,
    mask_sensitive_data,
    mask_dict,
    LogContext,
    log_function_call,
    log_business_event,
    log_api_request,
    log_data_flow,
    log_branch_decision,
    LogLevel,
    UNIFIED_LOG_DIR,
    cleanup_old_logs,
    cleanup_root_log_files,
    get_service_log_dir,
)

_rag_logger = None
_performance_monitor = None
_log_analyzer = None


class RAGLogger:
    """RAG专用日志器"""
    
    def __init__(self):
        self.logger = get_logger("rag")
    
    def log_query(self, query: str, metadata: Dict[str, Any] = None):
        """记录查询日志"""
        self.logger.info(f"[查询] {query}", extra={'extra_data': metadata or {}})
    
    def log_retrieval(self, query: str, filter_conditions: Dict[str, Any], 
                      result_count: int, duration_ms: int):
        """记录检索日志"""
        self.logger.info(
            f"[检索] 查询: {query[:50]}... | 过滤: {filter_conditions} | 结果数: {result_count} | 耗时: {duration_ms}ms",
            extra={'extra_data': {
                'query': query,
                'filter_conditions': filter_conditions,
                'result_count': result_count,
                'duration_ms': duration_ms
            }}
        )
    
    def log_rerank(self, input_count: int, output_count: int, 
                   top_score: float, duration_ms: int):
        """记录重排日志"""
        self.logger.info(
            f"[重排] 输入: {input_count} | 输出: {output_count} | 最高分: {top_score:.3f} | 耗时: {duration_ms}ms",
            extra={'extra_data': {
                'input_count': input_count,
                'output_count': output_count,
                'top_score': top_score,
                'duration_ms': duration_ms
            }}
        )
    
    def log_competition_match(self, input_name: str, matched_name: str, 
                               match_score: float, competition_type: str):
        """记录竞赛匹配日志"""
        self.logger.info(
            f"[竞赛匹配] 输入: {input_name} | 匹配: {matched_name} | 得分: {match_score:.1f} | 类型: {competition_type}",
            extra={'extra_data': {
                'input_name': input_name,
                'matched_name': matched_name,
                'match_score': match_score,
                'competition_type': competition_type
            }}
        )
    
    def log_document_load(self, source: str, doc_count: int, 
                          chunk_count: int, duration_ms: int):
        """记录文档加载日志"""
        self.logger.info(
            f"[文档加载] 来源: {source} | 文档数: {doc_count} | 分块数: {chunk_count} | 耗时: {duration_ms}ms",
            extra={'extra_data': {
                'source': source,
                'doc_count': doc_count,
                'chunk_count': chunk_count,
                'duration_ms': duration_ms
            }}
        )
    
    def log_performance(self, operation: str, duration_ms: int, 
                        details: Dict[str, Any] = None):
        """记录性能日志"""
        self.logger.debug(
            f"[性能] {operation} | 耗时: {duration_ms}ms",
            extra={'extra_data': details or {}}
        )
    
    def log_error(self, operation: str, error: Exception, 
                  context: Dict[str, Any] = None):
        """记录错误日志"""
        self.logger.error(
            f"[错误] {operation} | {type(error).__name__}: {error}",
            extra={'extra_data': context or {}},
            exc_info=True
        )


@dataclass
class OperationStats:
    """操作统计数据"""
    count: int = 0
    total_time_ms: float = 0
    max_time_ms: float = 0
    min_time_ms: float = float('inf')
    success_count: int = 0
    error_count: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_details: int = 100):
        self._operations: Dict[str, OperationStats] = {}
        self._lock = threading.Lock()
        self._max_details = max_details
    
    def record(self, operation: str, duration_ms: float, 
               success: bool = True, details: Dict[str, Any] = None):
        """记录操作性能"""
        with self._lock:
            if operation not in self._operations:
                self._operations[operation] = OperationStats()
            
            stats = self._operations[operation]
            stats.count += 1
            stats.total_time_ms += duration_ms
            stats.max_time_ms = max(stats.max_time_ms, duration_ms)
            stats.min_time_ms = min(stats.min_time_ms, duration_ms)
            
            if success:
                stats.success_count += 1
            else:
                stats.error_count += 1
            
            if details and len(stats.details) < self._max_details:
                stats.details.append({
                    'timestamp': datetime.now().isoformat(),
                    'duration_ms': duration_ms,
                    'success': success,
                    **details
                })
    
    def get_stats(self, operation: str = None, last_n: int = None) -> Optional[Dict[str, Any]]:
        """获取操作统计"""
        with self._lock:
            if operation:
                if operation not in self._operations:
                    return None
                stats = self._operations[operation]
                return {
                    'operation': operation,
                    'count': stats.count,
                    'avg_time_ms': round(stats.total_time_ms / stats.count, 2) if stats.count > 0 else 0,
                    'max_time_ms': round(stats.max_time_ms, 2),
                    'min_time_ms': round(stats.min_time_ms, 2) if stats.min_time_ms != float('inf') else 0,
                    'success_rate': round(stats.success_count / stats.count * 100, 2) if stats.count > 0 else 0,
                    'details': stats.details[-last_n:] if last_n else stats.details
                }
            else:
                return {
                    op: {
                        'count': s.count,
                        'avg_time_ms': round(s.total_time_ms / s.count, 2) if s.count > 0 else 0,
                        'max_time_ms': round(s.max_time_ms, 2),
                        'min_time_ms': round(s.min_time_ms, 2) if s.min_time_ms != float('inf') else 0,
                    }
                    for op, s in self._operations.items()
                }
    
    def get_slow_operations(self, threshold_ms: float = 1000) -> List[Dict[str, Any]]:
        """获取慢操作列表"""
        with self._lock:
            slow_ops = []
            for op, stats in self._operations.items():
                if stats.max_time_ms >= threshold_ms:
                    slow_ops.append({
                        'operation': op,
                        'max_time_ms': round(stats.max_time_ms, 2),
                        'avg_time_ms': round(stats.total_time_ms / stats.count, 2) if stats.count > 0 else 0,
                        'count': stats.count
                    })
            return sorted(slow_ops, key=lambda x: x['max_time_ms'], reverse=True)
    
    def get_operations_summary(self) -> Dict[str, Any]:
        """获取操作摘要"""
        with self._lock:
            if not self._operations:
                return {}
            
            total_ops = sum(s.count for s in self._operations.values())
            total_time = sum(s.total_time_ms for s in self._operations.values())
            
            return {
                'total_operations': total_ops,
                'total_time_ms': round(total_time, 2),
                'unique_operations': len(self._operations),
                'operations': list(self._operations.keys())
            }
    
    def clear(self):
        """清除所有统计"""
        with self._lock:
            self._operations.clear()


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or UNIFIED_LOG_DIR / "rag"
        self.logger = get_logger("log_analyzer")
    
    def search_logs(self, keyword: str = None, level: str = None, 
                    limit: int = 100) -> List[Dict[str, Any]]:
        """搜索日志"""
        results = []
        
        try:
            if not self.log_dir.exists():
                return results
            
            for log_file in self.log_dir.glob("*.log"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if keyword and keyword.lower() not in line.lower():
                                continue
                            if level and level.upper() not in line:
                                continue
                            
                            results.append({
                                'file': str(log_file.name),
                                'line': line.strip()
                            })
                            
                            if len(results) >= limit:
                                return results
                except Exception as e:
                    self.logger.warning(f"读取日志文件失败: {log_file}: {e}")
        except Exception as e:
            self.logger.error(f"搜索日志失败: {e}")
        
        return results
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误摘要"""
        error_count = 0
        error_types = {}
        
        try:
            if not self.log_dir.exists():
                return {'error_count': 0, 'error_types': {}}
            
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            
            for log_file in self.log_dir.glob("error_*.log"):
                try:
                    if log_file.stat().st_mtime < cutoff_time:
                        continue
                    
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if 'ERROR' in line or 'CRITICAL' in line:
                                error_count += 1
                                
                                for err_type in ['ValueError', 'KeyError', 'TypeError', 
                                                  'AttributeError', 'ImportError', 'Exception']:
                                    if err_type in line:
                                        error_types[err_type] = error_types.get(err_type, 0) + 1
                                        break
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning(f"获取错误摘要失败: {e}")
        
        return {
            'error_count': error_count,
            'error_types': error_types,
            'hours': hours
        }


def track_performance(operation: str):
    """性能追踪装饰器"""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                get_performance_monitor().record(operation, duration_ms, True)
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                get_performance_monitor().record(operation, duration_ms, False, {'error': str(e)})
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                get_performance_monitor().record(operation, duration_ms, True)
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                get_performance_monitor().record(operation, duration_ms, False, {'error': str(e)})
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


class RequestContext:
    """请求上下文管理器"""
    
    def __init__(self, request_id: str = None, user_id: str = None, operation: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.operation = operation
        self._old_values = {}
    
    def __enter__(self):
        if self.request_id:
            self._old_values['request_id'] = get_request_id()
            set_request_id(self.request_id)
        if self.user_id:
            self._old_values['user_id'] = get_user_id()
            set_user_id(self.user_id)
        if self.operation:
            self._old_values['operation'] = get_operation()
            set_operation(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for key, old_value in self._old_values.items():
            if key == 'request_id':
                set_request_id(old_value)
            elif key == 'user_id':
                set_user_id(old_value)
            elif key == 'operation':
                set_operation(old_value)
        return False


def get_rag_logger() -> RAGLogger:
    """获取RAG服务专用日志器"""
    global _rag_logger
    if _rag_logger is None:
        _rag_logger = RAGLogger()
    return _rag_logger


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_log_analyzer() -> LogAnalyzer:
    """获取日志分析器"""
    global _log_analyzer
    if _log_analyzer is None:
        _log_analyzer = LogAnalyzer()
    return _log_analyzer


rag_logger = get_rag_logger()
performance_monitor = get_performance_monitor()
log_analyzer = get_log_analyzer()


__all__ = [
    'setup_logging',
    'get_logger',
    'get_rag_logger',
    'rag_logger',
    'performance_monitor',
    'log_analyzer',
    'track_performance',
    'RequestContext',
    'set_request_id',
    'get_request_id',
    'set_user_id',
    'get_user_id',
    'set_session_id',
    'get_session_id',
    'set_operation',
    'get_operation',
    'clear_context',
    'mask_sensitive_data',
    'mask_dict',
    'LogContext',
    'log_function_call',
    'log_business_event',
    'log_api_request',
    'log_data_flow',
    'log_branch_decision',
    'LogLevel',
    'UNIFIED_LOG_DIR',
    'cleanup_old_logs',
    'cleanup_root_log_files',
    'get_service_log_dir',
]
