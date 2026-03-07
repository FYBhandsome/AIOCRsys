#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR资源优化测试

测试OCR模型池、资源监控和资源管理功能。
"""
import pytest
import asyncio
import gc
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conftest import API_PREFIX, TEST_STUDENTS


class TestOCRModelPool:
    """OCR模型池测试类"""
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_model_pool_singleton(self, test_logger):
        """测试模型池单例模式"""
        from app.services.ocr_model_pool import get_ocr_model_pool, OCRModelPool
        
        pool1 = get_ocr_model_pool()
        pool2 = get_ocr_model_pool()
        
        assert pool1 is pool2, "模型池应该是单例"
        assert isinstance(pool1, OCRModelPool), "应该返回OCRModelPool实例"
        
        test_logger.info("✓ 模型池单例模式测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_model_pool_configure(self, test_logger):
        """测试模型池配置"""
        from app.services.ocr_model_pool import get_ocr_model_pool
        
        pool = get_ocr_model_pool()
        pool.configure(
            use_gpu=False,
            lang="ch",
            max_instances=1
        )
        
        status = pool.get_status()
        assert status["max_instances"] == 1, "最大实例数应该为1"
        
        test_logger.info("✓ 模型池配置测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_model_pool_status(self, test_logger):
        """测试模型池状态获取"""
        from app.services.ocr_model_pool import get_ocr_model_pool
        
        pool = get_ocr_model_pool()
        status = pool.get_status()
        
        assert "preloaded" in status, "状态应包含preloaded字段"
        assert "max_instances" in status, "状态应包含max_instances字段"
        assert "total_instances" in status, "状态应包含total_instances字段"
        assert "stats" in status, "状态应包含stats字段"
        
        test_logger.info(f"模型池状态: {status}")
        test_logger.info("✓ 模型池状态获取测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_model_pool_health_check(self, test_logger):
        """测试模型池健康检查"""
        from app.services.ocr_model_pool import get_ocr_model_pool
        
        pool = get_ocr_model_pool()
        health = pool.health_check()
        
        assert "healthy" in health, "健康检查应包含healthy字段"
        assert "status" in health, "健康检查应包含status字段"
        assert "message" in health, "健康检查应包含message字段"
        
        test_logger.info(f"健康检查结果: {health}")
        test_logger.info("✓ 模型池健康检查测试通过")


class TestResourceMonitor:
    """资源监控测试类"""
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_resource_monitor_singleton(self, test_logger):
        """测试资源监控器单例模式"""
        from app.core.resource_monitor import get_resource_monitor, ResourceMonitor
        
        monitor1 = get_resource_monitor()
        monitor2 = get_resource_monitor()
        
        assert monitor1 is monitor2, "资源监控器应该是单例"
        assert isinstance(monitor1, ResourceMonitor), "应该返回ResourceMonitor实例"
        
        test_logger.info("✓ 资源监控器单例模式测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_take_snapshot(self, test_logger):
        """测试资源快照"""
        from app.core.resource_monitor import get_resource_monitor
        
        monitor = get_resource_monitor()
        snapshot = monitor.take_snapshot()
        
        assert snapshot.timestamp is not None, "快照应包含时间戳"
        assert snapshot.memory_rss_mb >= 0, "内存使用应大于等于0"
        assert snapshot.thread_count >= 1, "线程数应大于等于1"
        
        test_logger.info(f"资源快照: 内存={snapshot.memory_rss_mb:.1f}MB, "
                        f"CPU={snapshot.cpu_percent:.1f}%, 线程={snapshot.thread_count}")
        test_logger.info("✓ 资源快照测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_get_current_status(self, test_logger):
        """测试获取当前状态"""
        from app.core.resource_monitor import get_resource_monitor
        
        monitor = get_resource_monitor()
        status = monitor.get_current_status()
        
        assert "current" in status, "状态应包含current字段"
        assert "uptime_seconds" in status, "状态应包含uptime_seconds字段"
        assert "ocr_stats" in status, "状态应包含ocr_stats字段"
        
        test_logger.info(f"当前状态: {status}")
        test_logger.info("✓ 获取当前状态测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_get_history(self, test_logger):
        """测试获取历史记录"""
        from app.core.resource_monitor import get_resource_monitor
        
        monitor = get_resource_monitor()
        
        monitor.take_snapshot()
        monitor.take_snapshot()
        monitor.take_snapshot()
        
        history = monitor.get_history(limit=10)
        
        assert isinstance(history, list), "历史记录应该是列表"
        assert len(history) >= 3, "应该至少有3条记录"
        
        test_logger.info(f"历史记录数量: {len(history)}")
        test_logger.info("✓ 获取历史记录测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_get_summary(self, test_logger):
        """测试获取资源摘要"""
        from app.core.resource_monitor import get_resource_monitor
        
        monitor = get_resource_monitor()
        summary = monitor.get_summary()
        
        assert "memory" in summary or "message" in summary, "摘要应包含memory字段或message字段"
        
        test_logger.info(f"资源摘要: {summary}")
        test_logger.info("✓ 获取资源摘要测试通过")


class TestOCRServiceStats:
    """OCR服务统计测试类"""
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_ocr_service_singleton(self, test_logger):
        """测试OCR服务单例模式"""
        from app.services.ocr_service import get_ocr_service, OCRService
        
        service1 = get_ocr_service()
        service2 = get_ocr_service()
        
        assert service1 is service2, "OCR服务应该是单例"
        assert isinstance(service1, OCRService), "应该返回OCRService实例"
        
        test_logger.info("✓ OCR服务单例模式测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_ocr_service_stats(self, test_logger):
        """测试OCR服务统计"""
        from app.services.ocr_service import get_ocr_service
        
        service = get_ocr_service()
        stats = service.get_stats()
        
        assert "total_requests" in stats, "统计应包含total_requests字段"
        assert "successful_requests" in stats, "统计应包含successful_requests字段"
        assert "failed_requests" in stats, "统计应包含failed_requests字段"
        assert "avg_time_ms" in stats, "统计应包含avg_time_ms字段"
        
        test_logger.info(f"OCR服务统计: {stats}")
        test_logger.info("✓ OCR服务统计测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_ocr_model_pool_status(self, test_logger):
        """测试OCR服务模型池状态"""
        from app.services.ocr_service import get_ocr_service
        
        service = get_ocr_service()
        status = service.get_model_pool_status()
        
        assert "status" in status or "preloaded" in status, "状态应包含status或preloaded字段"
        
        test_logger.info(f"模型池状态: {status}")
        test_logger.info("✓ OCR服务模型池状态测试通过")


class TestExecutorManager:
    """线程池执行器测试类"""
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_executor_singleton(self, test_logger):
        """测试执行器单例模式"""
        from app.core.executor_manager import executor_manager, ExecutorManager
        
        assert isinstance(executor_manager, ExecutorManager), "应该是ExecutorManager实例"
        
        test_logger.info("✓ 执行器单例模式测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_executor_status(self, test_logger):
        """测试执行器状态"""
        from app.core.executor_manager import get_executor_status
        
        status = get_executor_status()
        
        assert "initialized" in status, "状态应包含initialized字段"
        assert "max_workers" in status, "状态应包含max_workers字段"
        assert "stats" in status, "状态应包含stats字段"
        
        test_logger.info(f"执行器状态: {status}")
        test_logger.info("✓ 执行器状态测试通过")


class TestResourceLeakDetection:
    """资源泄漏检测测试类"""
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_memory_stability(self, test_logger, check_resource_leak):
        """测试内存稳定性"""
        from app.core.resource_monitor import get_resource_monitor
        
        monitor = get_resource_monitor()
        
        check_resource_leak.snapshot("初始状态")
        
        for i in range(5):
            monitor.take_snapshot()
            await asyncio.sleep(0.1)
        
        gc.collect()
        check_resource_leak.snapshot("测试后状态")
        
        result = check_resource_leak.check(threshold_memory_mb=50, threshold_threads=5)
        
        test_logger.info(f"资源泄漏检查结果: {result}")
        
        assert not result["leak_detected"], f"检测到资源泄漏: {result}"
        
        test_logger.info("✓ 内存稳定性测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_concurrent_snapshots(self, test_logger):
        """测试并发快照"""
        from app.core.resource_monitor import get_resource_monitor
        import threading
        
        monitor = get_resource_monitor()
        errors = []
        
        def take_multiple_snapshots():
            try:
                for _ in range(10):
                    monitor.take_snapshot()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=take_multiple_snapshots) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"并发快照出错: {errors}"
        
        test_logger.info("✓ 并发快照测试通过")


class TestResourceReport:
    """资源报告测试类"""
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_json_report_generation(self, test_logger, resource_report_generator):
        """测试JSON报告生成"""
        report = resource_report_generator.generate_json_report(
            include_history=True,
            include_alerts=True
        )
        
        assert "report_type" in report, "报告应包含report_type字段"
        assert "generated_at" in report, "报告应包含generated_at字段"
        assert "summary" in report, "报告应包含summary字段"
        assert "current_status" in report, "报告应包含current_status字段"
        
        test_logger.info(f"JSON报告生成成功，包含字段: {list(report.keys())}")
        test_logger.info("✓ JSON报告生成测试通过")
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_html_report_generation(self, test_logger, resource_report_generator):
        """测试HTML报告生成"""
        html = resource_report_generator.generate_html_report(include_history=True)
        
        assert "<!DOCTYPE html>" in html, "HTML报告应包含DOCTYPE声明"
        assert "<html" in html, "HTML报告应包含html标签"
        assert "</html>" in html, "HTML报告应包含闭合html标签"
        assert "OCR服务资源使用报告" in html, "HTML报告应包含标题"
        
        test_logger.info(f"HTML报告生成成功，长度: {len(html)}字符")
        test_logger.info("✓ HTML报告生成测试通过")


class TestContinuousOCR:
    """连续OCR操作测试类"""
    
    @pytest.mark.ocr
    @pytest.mark.asyncio
    async def test_sequential_ocr_operations(self, test_logger, check_resource_leak):
        """测试连续OCR操作的资源稳定性"""
        from app.core.resource_monitor import get_resource_monitor
        from app.services.ocr_service import get_ocr_service
        
        monitor = get_resource_monitor()
        ocr_service = get_ocr_service()
        
        check_resource_leak.snapshot("连续OCR操作前")
        
        test_photo_dir = Path(__file__).parent.parent / "testphoto" / "test"
        
        if test_photo_dir.exists():
            photos = list(test_photo_dir.glob("*.jpg"))[:3]
            
            for i, photo_path in enumerate(photos):
                try:
                    result = ocr_service.recognize_text(str(photo_path))
                    test_logger.info(f"OCR操作 {i+1}: 检测到 {len(result)} 个文本块")
                except Exception as e:
                    test_logger.warning(f"OCR操作 {i+1} 失败: {e}")
                
                await asyncio.sleep(0.5)
        else:
            test_logger.warning("测试照片目录不存在，跳过实际OCR操作")
            for i in range(3):
                monitor.record_ocr_operation(100.0)
                await asyncio.sleep(0.5)
        
        gc.collect()
        check_resource_leak.snapshot("连续OCR操作后")
        
        result = check_resource_leak.check(threshold_memory_mb=100, threshold_threads=10)
        
        test_logger.info(f"连续OCR操作资源检查: {result}")
        
        test_logger.info("✓ 连续OCR操作测试通过")
