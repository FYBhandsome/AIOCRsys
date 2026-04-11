#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书处理工作流测试执行脚本
============================

执行完整的证书处理工作流测试，包括:
1. 正常流程测试
2. 边界情况测试
3. 性能测试
4. 生成详细的测试报告

使用方法:
    python run_workflow_tests.py [--mode MODE] [--output-dir DIR]

参数:
    --mode: 测试模式 (full/quick/edge-cases)
    --output-dir: 测试报告输出目录
"""

import asyncio
import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_certificate_workflow import (
    CertificateWorkflowTester,
    EdgeCaseTester,
    TestMetricsCollector,
    WorkflowTestResult
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowTestRunner:
    """工作流测试运行器"""
    
    def __init__(self, output_dir: str = "logs/workflow_tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics = TestMetricsCollector()
        
    async def run_full_tests(self):
        """运行完整测试套件"""
        logger.info("=" * 80)
        logger.info("开始运行完整工作流测试套件")
        logger.info("=" * 80)
        
        self.metrics.start_time = datetime.now().timestamp()
        
        # 运行边界情况测试
        await self._run_edge_case_tests()
        
        # 运行正常流程测试
        await self._run_normal_workflow_tests()
        
        # 运行性能测试
        await self._run_performance_tests()
        
        self.metrics.end_time = datetime.now().timestamp()
        
        # 生成报告
        self._generate_final_report()
        
    async def run_quick_tests(self):
        """运行快速测试（仅测试关键功能）"""
        logger.info("=" * 80)
        logger.info("开始运行快速测试")
        logger.info("=" * 80)
        
        self.metrics.start_time = datetime.now().timestamp()
        
        # 仅运行边界情况测试
        await self._run_edge_case_tests()
        
        self.metrics.end_time = datetime.now().timestamp()
        
        # 生成报告
        self._generate_final_report()
        
    async def run_edge_case_tests_only(self):
        """仅运行边界情况测试"""
        logger.info("=" * 80)
        logger.info("开始运行边界情况测试")
        logger.info("=" * 80)
        
        self.metrics.start_time = datetime.now().timestamp()
        
        await self._run_edge_case_tests()
        
        self.metrics.end_time = datetime.now().timestamp()
        
        # 生成报告
        self._generate_final_report()
        
    async def _run_edge_case_tests(self):
        """运行边界情况测试"""
        logger.info("\n" + "=" * 80)
        logger.info("阶段 1: 边界情况测试")
        logger.info("=" * 80)
        
        try:
            from httpx import AsyncClient
            from app.core.auth import create_access_token
            
            # 创建测试客户端
            async with AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
                # 创建测试token
                test_token = create_access_token(
                    data={"sub": "test_user", "role": "student"}
                )
                
                tester = EdgeCaseTester(client, test_token)
                
                # 测试用例列表
                test_cases = [
                    ("无法读取的证书", tester.test_unreadable_certificate),
                    ("OCR提取失败", tester.test_ocr_failure),
                    ("RAG检索错误", tester.test_rag_error),
                    ("AI模型超时", tester.test_ai_model_timeout)
                ]
                
                for case_name, test_func in test_cases:
                    logger.info(f"\n测试边界情况: {case_name}")
                    
                    try:
                        result = await test_func()
                        self.metrics.add_result(result)
                        
                        logger.info(
                            f"结果: {'✓ 通过' if result.success else '✗ 失败'}, "
                            f"耗时: {result.duration_ms:.2f}ms"
                        )
                        
                        if not result.success:
                            logger.error(f"错误详情: {result.errors}")
                            
                    except Exception as e:
                        logger.error(f"测试执行失败: {e}", exc_info=True)
                        # 创建失败结果
                        fail_result = WorkflowTestResult()
                        fail_result.test_name = f"边界测试 - {case_name}"
                        fail_result.success = False
                        fail_result.errors.append(f"测试执行异常: {str(e)}")
                        self.metrics.add_result(fail_result)
                        
        except Exception as e:
            logger.error(f"边界情况测试阶段失败: {e}", exc_info=True)
            
    async def _run_normal_workflow_tests(self):
        """运行正常工作流测试"""
        logger.info("\n" + "=" * 80)
        logger.info("阶段 2: 正常工作流测试")
        logger.info("=" * 80)
        
        try:
            from httpx import AsyncClient
            from app.core.auth import create_access_token
            
            # 查找测试照片目录
            test_photo_dirs = [
                project_root / "visual_model" / "testphoto",
                project_root / "tests" / "test_photos",
                project_root / "test_photos"
            ]
            
            test_photo_dir = None
            for dir_path in test_photo_dirs:
                if dir_path.exists():
                    test_photo_dir = dir_path
                    break
                    
            if not test_photo_dir:
                logger.warning("未找到测试照片目录，跳过正常工作流测试")
                return
                
            # 获取测试照片
            test_photos = list(test_photo_dir.glob("*.jpg")) + list(test_photo_dir.glob("*.png"))
            
            if not test_photos:
                logger.warning("未找到测试照片，跳过正常工作流测试")
                return
                
            logger.info(f"找到 {len(test_photos)} 张测试照片")
            
            # 创建测试客户端
            async with AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
                # 创建测试token
                test_token = create_access_token(
                    data={"sub": "test_user", "role": "student"}
                )
                
                tester = CertificateWorkflowTester(client, test_token)
                
                # 测试前5张照片
                for i, photo_path in enumerate(test_photos[:5], 1):
                    logger.info(f"\n测试照片 {i}/5: {photo_path.name}")
                    
                    try:
                        result = await tester.test_complete_workflow(
                            image_path=str(photo_path),
                            student_id="2024001"
                        )
                        
                        self.metrics.add_result(result)
                        
                        logger.info(
                            f"结果: {'✓ 成功' if result.success else '✗ 失败'}, "
                            f"耗时: {result.duration_ms:.2f}ms"
                        )
                        
                        if result.success:
                            logger.info(
                                f"  - 类别: {result.metrics.get('final_category')}, "
                                f"分数: {result.metrics.get('final_score')}, "
                                f"置信度: {result.metrics.get('ocr_confidence'):.2f}"
                            )
                        else:
                            logger.error(f"  错误: {result.errors}")
                            
                    except Exception as e:
                        logger.error(f"测试照片失败: {e}", exc_info=True)
                        
        except Exception as e:
            logger.error(f"正常工作流测试阶段失败: {e}", exc_info=True)
            
    async def _run_performance_tests(self):
        """运行性能测试"""
        logger.info("\n" + "=" * 80)
        logger.info("阶段 3: 性能测试")
        logger.info("=" * 80)
        
        try:
            from httpx import AsyncClient
            from app.core.auth import create_access_token
            
            # 查找测试照片
            test_photo_dirs = [
                project_root / "visual_model" / "testphoto",
                project_root / "tests" / "test_photos",
                project_root / "test_photos"
            ]
            
            test_photo_dir = None
            for dir_path in test_photo_dirs:
                if dir_path.exists():
                    test_photo_dir = dir_path
                    break
                    
            if not test_photo_dir:
                logger.warning("未找到测试照片目录，跳过性能测试")
                return
                
            test_photos = list(test_photo_dir.glob("*.jpg"))
            
            if not test_photos:
                logger.warning("未找到测试照片，跳过性能测试")
                return
                
            # 创建测试客户端
            async with AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
                test_token = create_access_token(
                    data={"sub": "test_user", "role": "student"}
                )
                
                tester = CertificateWorkflowTester(client, test_token)
                
                # 单次处理性能测试
                logger.info("\n测试单次处理性能...")
                photo_path = test_photos[0]
                
                result = await tester.test_complete_workflow(
                    image_path=str(photo_path),
                    student_id="2024001"
                )
                
                logger.info(f"单次处理耗时: {result.duration_ms:.2f}ms")
                
                if result.duration_ms > 10000:
                    logger.warning(f"⚠️ 处理时间过长: {result.duration_ms}ms")
                else:
                    logger.info(f"✓ 处理时间在可接受范围内")
                    
                # 并发处理性能测试
                logger.info("\n测试并发处理性能...")
                concurrent_tasks = []
                
                for photo in test_photos[:3]:
                    task = tester.test_complete_workflow(
                        image_path=str(photo),
                        student_id="2024001"
                    )
                    concurrent_tasks.append(task)
                    
                start_time = datetime.now().timestamp()
                results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
                total_duration = (datetime.now().timestamp() - start_time) * 1000
                
                successful = sum(
                    1 for r in results 
                    if isinstance(r, WorkflowTestResult) and r.success
                )
                
                logger.info(
                    f"并发处理结果: 成功 {successful}/{len(concurrent_tasks)}, "
                    f"总耗时: {total_duration:.2f}ms"
                )
                
                # 添加性能测试结果到指标
                for r in results:
                    if isinstance(r, WorkflowTestResult):
                        self.metrics.add_result(r)
                        
        except Exception as e:
            logger.error(f"性能测试阶段失败: {e}", exc_info=True)
            
    def _generate_final_report(self):
        """生成最终测试报告"""
        logger.info("\n" + "=" * 80)
        logger.info("生成测试报告")
        logger.info("=" * 80)
        
        # 生成文本报告
        report_path = self.output_dir / f"workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.metrics.save_report(str(report_path))
        
        # 打印报告摘要
        stats = self.metrics.calculate_statistics()
        
        logger.info("\n" + "=" * 80)
        logger.info("测试摘要")
        logger.info("=" * 80)
        logger.info(f"测试总数: {stats.get('total_tests', 0)}")
        logger.info(f"成功数量: {stats.get('successful_tests', 0)}")
        logger.info(f"失败数量: {stats.get('failed_tests', 0)}")
        logger.info(f"成功率: {stats.get('success_rate', 0)}%")
        logger.info(f"平均耗时: {stats.get('duration_stats', {}).get('avg_ms', 0)} ms")
        logger.info(f"测试总时长: {stats.get('test_duration_seconds', 0)} 秒")
        
        if stats.get('error_types'):
            logger.info("\n错误类型统计:")
            for error_type, count in stats['error_types'].items():
                logger.info(f"  - {error_type}: {count} 次")
                
        logger.info(f"\n详细报告已保存至: {report_path}")
        logger.info(f"JSON结果已保存至: {str(report_path).replace('.txt', '.json')}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='证书处理工作流测试执行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python run_workflow_tests.py                    # 运行完整测试
  python run_workflow_tests.py --mode quick       # 运行快速测试
  python run_workflow_tests.py --mode edge-cases  # 仅运行边界情况测试
        '''
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'quick', 'edge-cases'],
        default='full',
        help='测试模式: full=完整测试, quick=快速测试, edge-cases=仅边界情况'
    )
    
    parser.add_argument(
        '--output-dir',
        default='logs/workflow_tests',
        help='测试报告输出目录'
    )
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = WorkflowTestRunner(output_dir=args.output_dir)
    
    # 根据模式运行测试
    if args.mode == 'full':
        await runner.run_full_tests()
    elif args.mode == 'quick':
        await runner.run_quick_tests()
    elif args.mode == 'edge-cases':
        await runner.run_edge_case_tests_only()
        
    logger.info("\n测试执行完成！")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        sys.exit(1)
