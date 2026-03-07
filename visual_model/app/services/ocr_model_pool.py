#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR模型池管理器

实现OCR模型的预加载、复用和池化管理，避免重复加载模型导致的资源消耗问题。
"""

import os
import threading
import time
import weakref
import gc
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from app.core.logger import logger
from config import settings

if 'DISABLE_MODEL_SOURCE_CHECK' not in os.environ:
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

try:
    from paddleocr import PaddleOCR
    PADDLE_OCR_AVAILABLE = True
except ImportError:
    logger.warning("PaddleOCR未安装，OCR功能将不可用")
    PADDLE_OCR_AVAILABLE = False
    PaddleOCR = None


class ModelState(Enum):
    """模型状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class MemoryMetrics:
    """内存指标数据类"""
    rss_mb: float = 0.0
    vms_mb: float = 0.0
    percent: float = 0.0
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rss_mb": round(self.rss_mb, 2),
            "vms_mb": round(self.vms_mb, 2),
            "percent": round(self.percent, 2),
            "timestamp": self.timestamp
        }


@dataclass
class ModelMemoryInfo:
    """模型内存信息"""
    estimated_size_mb: float = 0.0
    loaded_at: Optional[datetime] = None
    last_memory_check: Optional[datetime] = None
    peak_memory_mb: float = 0.0


class ModelInstance:
    """模型实例封装"""
    
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        self.instance_id = instance_id
        self.config = config
        self.model: Optional[Any] = None
        self.state = ModelState.UNINITIALIZED
        self.created_at: Optional[datetime] = None
        self.last_used_at: Optional[datetime] = None
        self.use_count = 0
        self.error_message: Optional[str] = None
        self._lock = threading.Lock()
        self._memory_info = ModelMemoryInfo()
        self._memory_before_load: float = 0.0
        self._weak_refs: List[weakref.ref] = []
    
    def _get_current_memory_mb(self) -> float:
        """获取当前进程内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def initialize(self) -> bool:
        """初始化模型实例"""
        if not PADDLE_OCR_AVAILABLE:
            self.state = ModelState.ERROR
            self.error_message = "PaddleOCR未安装"
            return False
        
        with self._lock:
            if self.state == ModelState.READY:
                return True
            
            self.state = ModelState.INITIALIZING
            try:
                self._memory_before_load = self._get_current_memory_mb()
                
                gc.collect()
                
                if 'DISABLE_MODEL_SOURCE_CHECK' not in os.environ:
                    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
                
                self.model = PaddleOCR(**self.config)
                self.state = ModelState.READY
                self.created_at = datetime.now()
                self.last_used_at = datetime.now()
                
                memory_after = self._get_current_memory_mb()
                self._memory_info.estimated_size_mb = max(0, memory_after - self._memory_before_load)
                self._memory_info.loaded_at = datetime.now()
                self._memory_info.last_memory_check = datetime.now()
                self._memory_info.peak_memory_mb = memory_after
                
                gc.collect()
                
                try:
                    logger.info(
                        f"OCR模型实例 {self.instance_id} 初始化成功, "
                        f"预估内存占用: {self._memory_info.estimated_size_mb:.1f}MB"
                    )
                except ValueError:
                    pass
                return True
                
            except Exception as e:
                self.state = ModelState.ERROR
                self.error_message = str(e)
                logger.error(f"OCR模型实例 {self.instance_id} 初始化失败: {e}", exc_info=True)
                return False
    
    def acquire(self) -> Optional[Any]:
        """获取模型实例（标记为忙碌）"""
        with self._lock:
            if self.state != ModelState.READY:
                return None
            self.state = ModelState.BUSY
            self.last_used_at = datetime.now()
            self.use_count += 1
            return self.model
    
    def release(self):
        """释放模型实例（标记为就绪）"""
        with self._lock:
            if self.state == ModelState.BUSY:
                self.state = ModelState.READY
    
    def cleanup(self):
        """清理模型资源"""
        with self._lock:
            if self.model is not None:
                try:
                    if hasattr(self.model, 'close'):
                        self.model.close()
                    del self.model
                    self.model = None
                except Exception as e:
                    logger.warning(f"清理模型实例 {self.instance_id} 时出错: {e}")
            
            self._weak_refs.clear()
            self.state = ModelState.UNINITIALIZED
            gc.collect()
    
    def update_memory_metrics(self) -> MemoryMetrics:
        """更新并返回当前内存指标"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            metrics = MemoryMetrics(
                rss_mb=mem_info.rss / (1024 * 1024),
                vms_mb=mem_info.vms / (1024 * 1024),
                percent=process.memory_percent(),
                timestamp=datetime.now().isoformat()
            )
            
            self._memory_info.last_memory_check = datetime.now()
            if metrics.rss_mb > self._memory_info.peak_memory_mb:
                self._memory_info.peak_memory_mb = metrics.rss_mb
            
            return metrics
        except Exception:
            return MemoryMetrics(timestamp=datetime.now().isoformat())
    
    def get_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        return {
            "instance_id": self.instance_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "use_count": self.use_count,
            "error_message": self.error_message,
            "memory_info": {
                "estimated_size_mb": round(self._memory_info.estimated_size_mb, 2),
                "peak_memory_mb": round(self._memory_info.peak_memory_mb, 2),
                "loaded_at": self._memory_info.loaded_at.isoformat() if self._memory_info.loaded_at else None,
                "last_memory_check": self._memory_info.last_memory_check.isoformat() if self._memory_info.last_memory_check else None
            }
        }


class OCRModelPool:
    """OCR模型池管理器
    
    功能:
    - 预加载机制: 应用启动时预初始化模型
    - 模型复用: 保持模型在内存中，避免重复加载
    - 池化管理: 支持多个模型实例
    - 资源隔离: 每个池实例独立管理资源
    - 状态监控: 跟踪模型使用状态
    - 健康检查: 定期检查模型可用性
    - 内存监控: 实时监控内存使用
    - 自动清理: 内存压力时自动释放资源
    """
    
    _instance: Optional['OCRModelPool'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(OCRModelPool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化模型池"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._pool_lock = threading.Lock()
        self._instances: Dict[str, ModelInstance] = {}
        self._default_config: Dict[str, Any] = {}
        self._max_instances = 1
        self._preloaded = False
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_wait_time_ms": 0,
            "created_at": datetime.now().isoformat(),
            "memory_alerts": 0,
            "gc_triggered": 0
        }
        
        self._memory_threshold_percent = getattr(settings, 'OCR_MEMORY_THRESHOLD_PERCENT', 80.0)
        self._idle_timeout_seconds = getattr(settings, 'OCR_MODEL_IDLE_TIMEOUT_SECONDS', 3600)
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_running = False
        self._memory_history: List[MemoryMetrics] = []
        self._max_memory_history = 100
        
        logger.info("OCR模型池管理器已创建")
    
    def configure(self, 
                  use_gpu: bool = False,
                  lang: str = "ch",
                  max_instances: int = 1,
                  **kwargs) -> None:
        """配置模型池
        
        Args:
            use_gpu: 是否使用GPU
            lang: 识别语言
            max_instances: 最大实例数
            **kwargs: 其他PaddleOCR参数
        """
        device = "gpu:0" if use_gpu else "cpu"
        
        self._default_config = {
            "lang": lang,
            "device": device,
        }
        
        if getattr(settings, 'OCR_USE_ANGLE_CLS', True):
            self._default_config["use_textline_orientation"] = True
        
        self._max_instances = max_instances
        
        logger.info(f"OCR模型池配置完成: device={device}, lang={lang}, max_instances={max_instances}")
    
    def preload(self) -> bool:
        """预加载模型
        
        在应用启动时调用，提前初始化模型避免首次请求延迟。
        
        Returns:
            是否预加载成功
        """
        if self._preloaded:
            logger.info("OCR模型池已预加载，跳过")
            return True
        
        if not PADDLE_OCR_AVAILABLE:
            logger.warning("PaddleOCR不可用，无法预加载")
            return False
        
        logger.info("开始预加载OCR模型...")
        start_time = time.time()
        
        with self._pool_lock:
            instance_id = "default_0"
            instance = ModelInstance(instance_id, self._default_config)
            
            if instance.initialize():
                self._instances[instance_id] = instance
                self._preloaded = True
                
                elapsed = time.time() - start_time
                logger.info(f"OCR模型预加载完成，耗时: {elapsed:.2f}秒")
                return True
            else:
                logger.error("OCR模型预加载失败")
                return False
    
    def acquire_model(self, timeout: float = 30.0) -> Optional[Any]:
        """获取可用的模型实例
        
        Args:
            timeout: 获取超时时间（秒）
            
        Returns:
            模型实例或None
        """
        self._stats["total_requests"] += 1
        start_time = time.time()
        
        while True:
            with self._pool_lock:
                logger.debug(f"尝试获取模型，当前实例数: {len(self._instances)}, 最大实例数: {self._max_instances}")
                
                for instance_id, instance in self._instances.items():
                    logger.debug(f"检查实例 {instance_id}, 状态: {instance.state}")
                    if instance.state == ModelState.READY:
                        model = instance.acquire()
                        if model is not None:
                            wait_time = (time.time() - start_time) * 1000
                            self._stats["successful_requests"] += 1
                            self._stats["total_wait_time_ms"] += wait_time
                            logger.debug(f"获取模型实例 {instance_id}，等待时间: {wait_time:.2f}ms")
                            return model
                
                if len(self._instances) < self._max_instances:
                    instance_id = f"default_{len(self._instances)}"
                    try:
                        logger.info(f"创建新模型实例 {instance_id}")
                    except ValueError:
                        pass
                    instance = ModelInstance(instance_id, self._default_config)
                    
                    if instance.initialize():
                        self._instances[instance_id] = instance
                        model = instance.acquire()
                        if model is not None:
                            wait_time = (time.time() - start_time) * 1000
                            self._stats["successful_requests"] += 1
                            self._stats["total_wait_time_ms"] += wait_time
                            try:
                                logger.info(f"创建并获取新模型实例 {instance_id}，耗时: {wait_time:.2f}ms")
                            except ValueError:
                                pass
                            return model
                    else:
                        try:
                            logger.error(f"模型实例 {instance_id} 初始化失败: {instance.error_message}")
                        except ValueError:
                            pass
            
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                break
            
            time.sleep(0.5)
        
        self._stats["failed_requests"] += 1
        try:
            logger.warning("无法获取可用的OCR模型实例")
        except ValueError:
            pass
        return None
    
    def release_model(self, model: Any) -> None:
        """释放模型实例
        
        Args:
            model: 要释放的模型实例
        """
        with self._pool_lock:
            for instance in self._instances.values():
                if instance.model is model:
                    instance.release()
                    logger.debug(f"释放模型实例 {instance.instance_id}")
                    self._check_memory_pressure()
                    return
    
    def _get_current_memory_metrics(self) -> MemoryMetrics:
        """获取当前内存指标"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            return MemoryMetrics(
                rss_mb=mem_info.rss / (1024 * 1024),
                vms_mb=mem_info.vms / (1024 * 1024),
                percent=process.memory_percent(),
                timestamp=datetime.now().isoformat()
            )
        except Exception:
            return MemoryMetrics(timestamp=datetime.now().isoformat())
    
    def _check_memory_pressure(self) -> bool:
        """检查内存压力并在必要时触发清理
        
        Returns:
            是否检测到内存压力
        """
        metrics = self._get_current_memory_metrics()
        
        self._memory_history.append(metrics)
        if len(self._memory_history) > self._max_memory_history:
            self._memory_history = self._memory_history[-self._max_memory_history:]
        
        if metrics.percent > self._memory_threshold_percent:
            self._stats["memory_alerts"] += 1
            logger.warning(
                f"内存使用率过高: {metrics.percent:.1f}% > {self._memory_threshold_percent}%"
            )
            
            collected = gc.collect()
            self._stats["gc_triggered"] += 1
            logger.info(f"触发垃圾回收，回收对象数: {collected}")
            
            return True
        
        return False
    
    def start_memory_monitor(self, interval: float = 30.0) -> None:
        """启动内存监控线程
        
        Args:
            interval: 监控间隔（秒）
        """
        if self._cleanup_running:
            logger.warning("内存监控已在运行")
            return
        
        self._cleanup_running = True
        
        def monitor_loop():
            while self._cleanup_running:
                try:
                    self._check_memory_pressure()
                    self._cleanup_idle_instances()
                except Exception as e:
                    logger.error(f"内存监控出错: {e}")
                time.sleep(interval)
        
        self._cleanup_thread = threading.Thread(
            target=monitor_loop,
            name="OCRMemoryMonitor",
            daemon=True
        )
        self._cleanup_thread.start()
        logger.info(f"内存监控已启动，间隔: {interval}秒")
    
    def stop_memory_monitor(self) -> None:
        """停止内存监控线程"""
        self._cleanup_running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)
            self._cleanup_thread = None
        logger.info("内存监控已停止")
    
    def _cleanup_idle_instances(self) -> None:
        """清理空闲超时的模型实例"""
        if self._idle_timeout_seconds <= 0:
            return
        
        now = datetime.now()
        instances_to_cleanup = []
        
        with self._pool_lock:
            for instance_id, instance in self._instances.items():
                if (instance.state == ModelState.READY and 
                    instance.last_used_at and
                    (now - instance.last_used_at).total_seconds() > self._idle_timeout_seconds):
                    if instance.use_count > 0:
                        instances_to_cleanup.append(instance_id)
        
        if instances_to_cleanup:
            logger.info(f"发现 {len(instances_to_cleanup)} 个空闲超时的模型实例")
            for instance_id in instances_to_cleanup:
                with self._pool_lock:
                    if instance_id in self._instances:
                        self._instances[instance_id].cleanup()
                        del self._instances[instance_id]
                        logger.info(f"已清理空闲模型实例: {instance_id}")
            
            gc.collect()
    
    def force_gc(self) -> int:
        """强制执行垃圾回收
        
        Returns:
            回收的对象数量
        """
        collected = gc.collect()
        logger.info(f"强制垃圾回收完成，回收对象数: {collected}")
        return collected
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        current = self._get_current_memory_metrics()
        
        total_estimated_mb = sum(
            inst._memory_info.estimated_size_mb 
            for inst in self._instances.values()
        )
        
        return {
            "current": current.to_dict(),
            "total_model_memory_mb": round(total_estimated_mb, 2),
            "memory_threshold_percent": self._memory_threshold_percent,
            "memory_alerts": self._stats["memory_alerts"],
            "gc_triggered": self._stats["gc_triggered"],
            "history_count": len(self._memory_history)
        }
    
    def cleanup(self) -> None:
        """清理所有模型资源"""
        logger.info("开始清理OCR模型池...")
        
        self.stop_memory_monitor()
        
        with self._pool_lock:
            for instance in self._instances.values():
                instance.cleanup()
            self._instances.clear()
            self._preloaded = False
            self._memory_history.clear()
        
        gc.collect()
        
        logger.info("OCR模型池清理完成")
    
    def get_status(self) -> Dict[str, Any]:
        """获取模型池状态"""
        with self._pool_lock:
            instances_status = [inst.get_status() for inst in self._instances.values()]
            
            ready_count = sum(1 for inst in self._instances.values() if inst.state == ModelState.READY)
            busy_count = sum(1 for inst in self._instances.values() if inst.state == ModelState.BUSY)
            error_count = sum(1 for inst in self._instances.values() if inst.state == ModelState.ERROR)
            
            avg_wait_time = (
                self._stats["total_wait_time_ms"] / self._stats["successful_requests"]
                if self._stats["successful_requests"] > 0 else 0
            )
            
            total_model_memory = sum(
                inst._memory_info.estimated_size_mb 
                for inst in self._instances.values()
            )
            
            return {
                "preloaded": self._preloaded,
                "max_instances": self._max_instances,
                "total_instances": len(self._instances),
                "ready_instances": ready_count,
                "busy_instances": busy_count,
                "error_instances": error_count,
                "instances": instances_status,
                "stats": {
                    **self._stats,
                    "avg_wait_time_ms": round(avg_wait_time, 2)
                },
                "memory": self.get_memory_stats(),
                "total_model_memory_mb": round(total_model_memory, 2)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = self.get_status()
        
        is_healthy = (
            self._preloaded and
            status["ready_instances"] > 0 and
            status["error_instances"] == 0
        )
        
        return {
            "healthy": is_healthy,
            "status": status,
            "message": "OCR模型池运行正常" if is_healthy else "OCR模型池存在问题"
        }


_ocr_model_pool_instance: Optional[OCRModelPool] = None
_pool_lock = threading.Lock()


def get_ocr_model_pool() -> OCRModelPool:
    """获取OCR模型池实例（单例模式）"""
    global _ocr_model_pool_instance
    
    if _ocr_model_pool_instance is None:
        with _pool_lock:
            if _ocr_model_pool_instance is None:
                _ocr_model_pool_instance = OCRModelPool()
    
    return _ocr_model_pool_instance


def reset_ocr_model_pool() -> None:
    """重置OCR模型池实例（用于测试）"""
    global _ocr_model_pool_instance
    
    with _pool_lock:
        if _ocr_model_pool_instance is not None:
            try:
                _ocr_model_pool_instance.cleanup()
            except Exception as e:
                logger.warning(f"清理OCR模型池时出错: {e}")
            _ocr_model_pool_instance = None
    
    logger.info("OCR模型池已重置")
