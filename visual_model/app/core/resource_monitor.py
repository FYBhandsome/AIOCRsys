#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源监控模块

提供内存、线程、CPU等关键指标的实时监控功能。
支持内存泄漏检测、内存趋势分析和自动告警。
"""

import gc
import os
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import logging

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from app.core.logger import logger


@dataclass
class ResourceSnapshot:
    """资源快照"""
    timestamp: str
    memory_rss_mb: float
    memory_vms_mb: float
    memory_percent: float
    cpu_percent: float
    thread_count: int
    available_memory_mb: float = 0.0
    gpu_memory_mb: float = 0.0
    gpu_memory_percent: float = 0.0
    gc_gen0: int = 0
    gc_gen1: int = 0
    gc_gen2: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "memory_rss_mb": round(self.memory_rss_mb, 2),
            "memory_vms_mb": round(self.memory_vms_mb, 2),
            "memory_percent": round(self.memory_percent, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "thread_count": self.thread_count,
            "available_memory_mb": round(self.available_memory_mb, 2),
            "gpu_memory_mb": round(self.gpu_memory_mb, 2),
            "gpu_memory_percent": round(self.gpu_memory_percent, 2),
            "gc_objects": {
                "gen0": self.gc_gen0,
                "gen1": self.gc_gen1,
                "gen2": self.gc_gen2
            }
        }


@dataclass
class MemoryTrend:
    """内存趋势数据"""
    samples: int = 0
    min_rss_mb: float = float('inf')
    max_rss_mb: float = 0.0
    avg_rss_mb: float = 0.0
    trend_direction: str = "stable"
    growth_rate_mb_per_min: float = 0.0
    potential_leak: bool = False


@dataclass
class AlertConfig:
    """告警配置"""
    memory_percent_threshold: float = 80.0
    cpu_percent_threshold: float = 90.0
    thread_count_threshold: int = 50
    gpu_memory_percent_threshold: float = 80.0
    memory_growth_threshold_mb_per_min: float = 50.0
    leak_detection_window_seconds: float = 300.0
    startup_grace_period_seconds: float = 300.0


@dataclass
class ResourceAlert:
    """资源告警"""
    timestamp: str
    alert_type: str
    current_value: float
    threshold: float
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "alert_type": self.alert_type,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "message": self.message
        }


class ResourceMonitor:
    """资源监控器
    
    功能:
    - 内存使用量监控 (RSS, VMS)
    - 线程数量监控
    - CPU占用率监控
    - GPU内存监控（可选）
    - 资源使用历史记录
    - 阈值告警机制
    - 内存泄漏检测
    - 内存趋势分析
    """
    
    _instance: Optional['ResourceMonitor'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ResourceMonitor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化资源监控器"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._snapshot_lock = threading.Lock()
        
        self._history: deque = deque(maxlen=1000)
        self._alerts: deque = deque(maxlen=100)
        
        self._alert_config = AlertConfig()
        self._alert_callbacks: List[Callable[[ResourceAlert], None]] = []
        
        self._process = None
        if PSUTIL_AVAILABLE:
            self._process = psutil.Process(os.getpid())
        
        self._start_time = datetime.now()
        self._ocr_operation_count = 0
        self._ocr_total_time_ms = 0.0
        
        self._memory_trend = MemoryTrend()
        self._last_gc_count = (0, 0, 0)
        
        logger.info("资源监控器已创建")
    
    def configure(self,
                  memory_percent_threshold: float = 80.0,
                  cpu_percent_threshold: float = 90.0,
                  thread_count_threshold: int = 50,
                  gpu_memory_percent_threshold: float = 80.0,
                  memory_growth_threshold_mb_per_min: float = 50.0,
                  leak_detection_window_seconds: float = 300.0,
                  startup_grace_period_seconds: float = 300.0) -> None:
        """配置告警阈值
        
        Args:
            memory_percent_threshold: 内存使用率告警阈值
            cpu_percent_threshold: CPU使用率告警阈值
            thread_count_threshold: 线程数告警阈值
            gpu_memory_percent_threshold: GPU显存使用率告警阈值
            memory_growth_threshold_mb_per_min: 内存增长速率告警阈值 (MB/分钟)
            leak_detection_window_seconds: 内存泄漏检测时间窗口（秒）
            startup_grace_period_seconds: 启动期豁免时间（秒）
        """
        self._alert_config = AlertConfig(
            memory_percent_threshold=memory_percent_threshold,
            cpu_percent_threshold=cpu_percent_threshold,
            thread_count_threshold=thread_count_threshold,
            gpu_memory_percent_threshold=gpu_memory_percent_threshold,
            memory_growth_threshold_mb_per_min=memory_growth_threshold_mb_per_min,
            leak_detection_window_seconds=leak_detection_window_seconds,
            startup_grace_period_seconds=startup_grace_period_seconds
        )
        logger.info(f"资源监控告警配置: 内存={memory_percent_threshold}%, CPU={cpu_percent_threshold}%, "
                   f"线程={thread_count_threshold}, GPU={gpu_memory_percent_threshold}%, "
                   f"内存增长阈值={memory_growth_threshold_mb_per_min}MB/min, "
                   f"启动豁免期={startup_grace_period_seconds}秒")
    
    def add_alert_callback(self, callback: Callable[[ResourceAlert], None]) -> None:
        """添加告警回调函数"""
        self._alert_callbacks.append(callback)
    
    def take_snapshot(self) -> ResourceSnapshot:
        """获取当前资源快照"""
        gc_counts = gc.get_count()
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.now().isoformat(),
            memory_rss_mb=0.0,
            memory_vms_mb=0.0,
            memory_percent=0.0,
            cpu_percent=0.0,
            thread_count=threading.active_count(),
            available_memory_mb=0.0,
            gpu_memory_mb=0.0,
            gpu_memory_percent=0.0,
            gc_gen0=gc_counts[0],
            gc_gen1=gc_counts[1],
            gc_gen2=gc_counts[2]
        )
        
        if PSUTIL_AVAILABLE and self._process:
            try:
                memory_info = self._process.memory_info()
                snapshot.memory_rss_mb = memory_info.rss / (1024 * 1024)
                snapshot.memory_vms_mb = memory_info.vms / (1024 * 1024)
                
                snapshot.memory_percent = self._process.memory_percent()
                snapshot.cpu_percent = self._process.cpu_percent(interval=0.1)
                
                virtual_memory = psutil.virtual_memory()
                snapshot.available_memory_mb = virtual_memory.available / (1024 * 1024)
                
            except Exception as e:
                logger.warning(f"获取资源信息失败: {e}")
        
        with self._snapshot_lock:
            self._history.append(snapshot)
        
        self._update_memory_trend()
        self._check_alerts(snapshot)
        
        return snapshot
    
    def _update_memory_trend(self) -> None:
        """更新内存趋势分析"""
        with self._snapshot_lock:
            history = list(self._history)
        
        if len(history) < 2:
            return
        
        uptime_seconds = (datetime.now() - self._start_time).total_seconds()
        if uptime_seconds < self._alert_config.startup_grace_period_seconds:
            return
        
        window_seconds = self._alert_config.leak_detection_window_seconds
        now = datetime.now()
        
        window_start = now - timedelta(seconds=window_seconds)
        
        window_samples = [
            s for s in history 
            if datetime.fromisoformat(s.timestamp) >= window_start
        ]
        
        if len(window_samples) < 2:
            return
        
        rss_values = [s.memory_rss_mb for s in window_samples]
        
        self._memory_trend.samples = len(window_samples)
        self._memory_trend.min_rss_mb = min(rss_values)
        self._memory_trend.max_rss_mb = max(rss_values)
        self._memory_trend.avg_rss_mb = sum(rss_values) / len(rss_values)
        
        first_rss = rss_values[0]
        last_rss = rss_values[-1]
        first_time = datetime.fromisoformat(window_samples[0].timestamp)
        last_time = datetime.fromisoformat(window_samples[-1].timestamp)
        
        time_diff_minutes = (last_time - first_time).total_seconds() / 60.0
        
        if time_diff_minutes > 0:
            self._memory_trend.growth_rate_mb_per_min = (last_rss - first_rss) / time_diff_minutes
        else:
            self._memory_trend.growth_rate_mb_per_min = 0.0
        
        if self._memory_trend.growth_rate_mb_per_min > 10:
            self._memory_trend.trend_direction = "increasing"
        elif self._memory_trend.growth_rate_mb_per_min < -10:
            self._memory_trend.trend_direction = "decreasing"
        else:
            self._memory_trend.trend_direction = "stable"
        
        self._memory_trend.potential_leak = (
            self._memory_trend.growth_rate_mb_per_min > 
            self._alert_config.memory_growth_threshold_mb_per_min
        )
    
    def _check_alerts(self, snapshot: ResourceSnapshot) -> None:
        """检查是否触发告警"""
        alerts = []
        
        if snapshot.memory_percent > self._alert_config.memory_percent_threshold:
            alert = ResourceAlert(
                timestamp=snapshot.timestamp,
                alert_type="memory",
                current_value=snapshot.memory_percent,
                threshold=self._alert_config.memory_percent_threshold,
                message=f"内存使用率过高: {snapshot.memory_percent:.1f}% > {self._alert_config.memory_percent_threshold}%"
            )
            alerts.append(alert)
        
        if snapshot.cpu_percent > self._alert_config.cpu_percent_threshold:
            alert = ResourceAlert(
                timestamp=snapshot.timestamp,
                alert_type="cpu",
                current_value=snapshot.cpu_percent,
                threshold=self._alert_config.cpu_percent_threshold,
                message=f"CPU使用率过高: {snapshot.cpu_percent:.1f}% > {self._alert_config.cpu_percent_threshold}%"
            )
            alerts.append(alert)
        
        if snapshot.thread_count > self._alert_config.thread_count_threshold:
            alert = ResourceAlert(
                timestamp=snapshot.timestamp,
                alert_type="thread",
                current_value=snapshot.thread_count,
                threshold=self._alert_config.thread_count_threshold,
                message=f"线程数量过多: {snapshot.thread_count} > {self._alert_config.thread_count_threshold}"
            )
            alerts.append(alert)
        
        if self._memory_trend.potential_leak:
            alert = ResourceAlert(
                timestamp=snapshot.timestamp,
                alert_type="memory_leak",
                current_value=self._memory_trend.growth_rate_mb_per_min,
                threshold=self._alert_config.memory_growth_threshold_mb_per_min,
                message=f"检测到潜在内存泄漏: 增长速率 {self._memory_trend.growth_rate_mb_per_min:.2f} MB/min"
            )
            alerts.append(alert)
        
        for alert in alerts:
            with self._snapshot_lock:
                self._alerts.append(alert)
            logger.warning(f"资源告警: {alert.message}")
            
            for callback in self._alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"告警回调执行失败: {e}")
    
    def start_monitoring(self, interval: float = 5.0) -> None:
        """启动后台监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self._monitoring:
            logger.warning("资源监控已在运行")
            return
        
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                try:
                    self.take_snapshot()
                except Exception as e:
                    logger.error(f"资源监控出错: {e}")
                time.sleep(interval)
        
        self._monitor_thread = threading.Thread(
            target=monitor_loop,
            name="ResourceMonitorThread",
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"资源监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self) -> None:
        """停止后台监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        logger.info("资源监控已停止")
    
    def record_ocr_operation(self, duration_ms: float) -> None:
        """记录OCR操作
        
        Args:
            duration_ms: 操作耗时（毫秒）
        """
        self._ocr_operation_count += 1
        self._ocr_total_time_ms += duration_ms
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前资源状态"""
        snapshot = self.take_snapshot()
        
        uptime = (datetime.now() - self._start_time).total_seconds()
        avg_ocr_time = (
            self._ocr_total_time_ms / self._ocr_operation_count
            if self._ocr_operation_count > 0 else 0
        )
        
        return {
            "current": snapshot.to_dict(),
            "uptime_seconds": round(uptime, 2),
            "ocr_stats": {
                "operation_count": self._ocr_operation_count,
                "total_time_ms": round(self._ocr_total_time_ms, 2),
                "avg_time_ms": round(avg_ocr_time, 2)
            },
            "monitoring": self._monitoring,
            "psutil_available": PSUTIL_AVAILABLE
        }
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            历史记录列表
        """
        with self._snapshot_lock:
            history = list(self._history)
        
        if limit > 0:
            history = history[-limit:]
        
        return [s.to_dict() for s in history]
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取告警记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            告警记录列表
        """
        with self._snapshot_lock:
            alerts = list(self._alerts)
        
        if limit > 0:
            alerts = alerts[-limit:]
        
        return [a.to_dict() for a in alerts]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取资源使用摘要"""
        with self._snapshot_lock:
            history = list(self._history)
        
        if not history:
            return {
                "message": "暂无历史数据",
                "start_time": self._start_time.isoformat()
            }
        
        memory_values = [s.memory_percent for s in history]
        cpu_values = [s.cpu_percent for s in history]
        thread_values = [s.thread_count for s in history]
        
        return {
            "start_time": self._start_time.isoformat(),
            "sample_count": len(history),
            "memory": {
                "min_percent": round(min(memory_values), 2),
                "max_percent": round(max(memory_values), 2),
                "avg_percent": round(sum(memory_values) / len(memory_values), 2),
                "current_mb": round(history[-1].memory_rss_mb, 2)
            },
            "cpu": {
                "min_percent": round(min(cpu_values), 2),
                "max_percent": round(max(cpu_values), 2),
                "avg_percent": round(sum(cpu_values) / len(cpu_values), 2)
            },
            "threads": {
                "min": min(thread_values),
                "max": max(thread_values),
                "current": thread_values[-1]
            },
            "ocr_stats": {
                "operation_count": self._ocr_operation_count,
                "avg_time_ms": round(
                    self._ocr_total_time_ms / self._ocr_operation_count
                    if self._ocr_operation_count > 0 else 0, 2
                )
            },
            "memory_trend": {
                "direction": self._memory_trend.trend_direction,
                "growth_rate_mb_per_min": round(self._memory_trend.growth_rate_mb_per_min, 2),
                "potential_leak": self._memory_trend.potential_leak,
                "samples": self._memory_trend.samples,
                "min_rss_mb": round(self._memory_trend.min_rss_mb, 2) if self._memory_trend.min_rss_mb != float('inf') else 0,
                "max_rss_mb": round(self._memory_trend.max_rss_mb, 2),
                "avg_rss_mb": round(self._memory_trend.avg_rss_mb, 2)
            }
        }
    
    def get_memory_trend(self) -> Dict[str, Any]:
        """获取内存趋势详情"""
        return {
            "direction": self._memory_trend.trend_direction,
            "growth_rate_mb_per_min": round(self._memory_trend.growth_rate_mb_per_min, 2),
            "potential_leak": self._memory_trend.potential_leak,
            "samples": self._memory_trend.samples,
            "min_rss_mb": round(self._memory_trend.min_rss_mb, 2) if self._memory_trend.min_rss_mb != float('inf') else 0,
            "max_rss_mb": round(self._memory_trend.max_rss_mb, 2),
            "avg_rss_mb": round(self._memory_trend.avg_rss_mb, 2),
            "threshold_mb_per_min": self._alert_config.memory_growth_threshold_mb_per_min
        }
    
    def force_gc(self) -> Dict[str, Any]:
        """强制执行垃圾回收并返回结果"""
        before = self.take_snapshot()
        
        collected = gc.collect()
        
        after = self.take_snapshot()
        
        return {
            "collected_objects": collected,
            "memory_before_mb": round(before.memory_rss_mb, 2),
            "memory_after_mb": round(after.memory_rss_mb, 2),
            "memory_freed_mb": round(before.memory_rss_mb - after.memory_rss_mb, 2),
            "gc_counts": {
                "gen0": after.gc_gen0,
                "gen1": after.gc_gen1,
                "gen2": after.gc_gen2
            }
        }
    
    def clear_history(self) -> None:
        """清空历史记录"""
        with self._snapshot_lock:
            self._history.clear()
            self._alerts.clear()
        logger.info("资源监控历史记录已清空")


_resource_monitor_instance: Optional[ResourceMonitor] = None
_monitor_lock = threading.Lock()


def get_resource_monitor() -> ResourceMonitor:
    """获取资源监控器实例（单例模式）"""
    global _resource_monitor_instance
    
    if _resource_monitor_instance is None:
        with _monitor_lock:
            if _resource_monitor_instance is None:
                _resource_monitor_instance = ResourceMonitor()
    
    return _resource_monitor_instance
