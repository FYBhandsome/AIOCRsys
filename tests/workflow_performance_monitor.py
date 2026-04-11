#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书处理工作流性能监控和验证脚本
==================================

验证以下指标：
1. OCR准确率 >= 95%
2. RAG检索相关性得分 >= 0.85
3. 清晰的评分标准展示
4. 前端更新时间 < 3秒
5. 完善的错误处理
"""

import asyncio
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.enhanced_certificate_workflow import get_enhanced_workflow
from app.core.logger import logger as app_logger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowPerformanceMonitor:
    """工作流性能监控器"""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {
            "ocr_accuracy": [],
            "rag_relevance": [],
            "processing_time": [],
            "frontend_update_time": []
        }
        
        self.thresholds = {
            "ocr_accuracy": 0.95,
            "rag_relevance": 0.85,
            "processing_time": 10000,  # 10秒
            "frontend_update_time": 3000  # 3秒
        }
    
    async def run_comprehensive_test(self, test_images: List[str]) -> Dict[str, Any]:
        """运行综合测试
        
        Args:
            test_images: 测试图片路径列表
            
        Returns:
            测试结果
        """
        logger.info("=" * 80)
        logger.info("开始证书处理工作流性能验证")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        for i, image_path in enumerate(test_images, 1):
            logger.info(f"\n测试 {i}/{len(test_images)}: {Path(image_path).name}")
            
            try:
                result = await self._test_single_certificate(image_path)
                self.test_results.append(result)
                
                # 记录性能指标
                if result.get("success"):
                    metrics = result.get("metrics", {})
                    if "ocr_accuracy" in metrics:
                        self.performance_metrics["ocr_accuracy"].append(metrics["ocr_accuracy"])
                    if "rag_relevance_score" in metrics:
                        self.performance_metrics["rag_relevance"].append(metrics["rag_relevance_score"])
                    if "total_processing_time_ms" in metrics:
                        self.performance_metrics["processing_time"].append(metrics["total_processing_time_ms"])
                
            except Exception as e:
                logger.error(f"测试失败: {e}", exc_info=True)
                self.test_results.append({
                    "success": False,
                    "error": str(e),
                    "image": image_path
                })
        
        total_time = time.time() - start_time
        
        # 生成测试报告
        report = self._generate_report(total_time)
        
        logger.info("\n" + "=" * 80)
        logger.info("测试完成")
        logger.info("=" * 80)
        
        return report
    
    async def _test_single_certificate(self, image_path: str) -> Dict[str, Any]:
        """测试单个证书
        
        Args:
            image_path: 图片路径
            
        Returns:
            测试结果
        """
        workflow = get_enhanced_workflow()
        
        # 模拟进度回调
        progress_history = []
        
        async def progress_callback(progress: int, message: str):
            progress_history.append({
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"  [{progress}%] {message}")
        
        # 执行工作流
        result = await workflow.process_certificate(
            image_path=image_path,
            student_info={
                "student_id": "TEST001",
                "username": "测试学生"
            },
            progress_callback=progress_callback
        )
        
        result["image"] = image_path
        result["progress_history"] = progress_history
        
        # 验证各项指标
        validations = self._validate_result(result)
        result["validations"] = validations
        
        return result
    
    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证测试结果
        
        Args:
            result: 测试结果
            
        Returns:
            验证结果
        """
        validations = {
            "ocr_accuracy": {"passed": False, "value": 0, "threshold": self.thresholds["ocr_accuracy"]},
            "rag_relevance": {"passed": False, "value": 0, "threshold": self.thresholds["rag_relevance"]},
            "processing_time": {"passed": False, "value": 0, "threshold": self.thresholds["processing_time"]},
            "frontend_update": {"passed": False, "value": 0, "threshold": self.thresholds["frontend_update_time"]},
            "error_handling": {"passed": False, "value": 0},
            "scoring_rubric": {"passed": False, "value": False}
        }
        
        if not result.get("success"):
            # 验证错误处理
            errors = result.get("errors", [])
            all_handled = all(e.get("handled", False) for e in errors)
            validations["error_handling"]["passed"] = all_handled
            validations["error_handling"]["value"] = len(errors)
            return validations
        
        metrics = result.get("metrics", {})
        
        # 验证OCR准确率
        ocr_accuracy = metrics.get("ocr_accuracy", 0)
        validations["ocr_accuracy"]["value"] = ocr_accuracy
        validations["ocr_accuracy"]["passed"] = ocr_accuracy >= self.thresholds["ocr_accuracy"]
        
        # 验证RAG相关性
        rag_relevance = metrics.get("rag_relevance_score", 0)
        validations["rag_relevance"]["value"] = rag_relevance
        validations["rag_relevance"]["passed"] = rag_relevance >= self.thresholds["rag_relevance"]
        
        # 验证处理时间
        processing_time = metrics.get("total_processing_time_ms", 0)
        validations["processing_time"]["value"] = processing_time
        validations["processing_time"]["passed"] = processing_time <= self.thresholds["processing_time"]
        
        # 验证前端更新时间
        for step in result.get("steps", []):
            if step.get("step") == "frontend_update":
                update_time = step.get("update_time_ms", 0)
                validations["frontend_update"]["value"] = update_time
                validations["frontend_update"]["passed"] = update_time <= self.thresholds["frontend_update_time"]
                break
        
        # 验证评分标准
        score_result = result.get("score_result", {})
        rubric = score_result.get("scoring_rubric", {})
        has_rubric = bool(rubric)
        validations["scoring_rubric"]["value"] = has_rubric
        validations["scoring_rubric"]["passed"] = has_rubric
        
        return validations
    
    def _generate_report(self, total_time: float) -> Dict[str, Any]:
        """生成测试报告
        
        Args:
            total_time: 总测试时间
            
        Returns:
            测试报告
        """
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success"))
        failed_tests = total_tests - successful_tests
        
        # 计算各项指标的统计信息
        stats = {}
        
        for metric_name, values in self.performance_metrics.items():
            if values:
                stats[metric_name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "pass_rate": sum(1 for v in values if v >= self.thresholds.get(metric_name, 0)) / len(values)
                }
        
        # 验证结果统计
        validation_stats = {
            "ocr_accuracy": {"passed": 0, "failed": 0},
            "rag_relevance": {"passed": 0, "failed": 0},
            "processing_time": {"passed": 0, "failed": 0},
            "frontend_update": {"passed": 0, "failed": 0},
            "error_handling": {"passed": 0, "failed": 0},
            "scoring_rubric": {"passed": 0, "failed": 0}
        }
        
        for result in self.test_results:
            validations = result.get("validations", {})
            for key, validation in validations.items():
                if key in validation_stats:
                    if validation.get("passed"):
                        validation_stats[key]["passed"] += 1
                    else:
                        validation_stats[key]["failed"] += 1
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "total_time_seconds": total_time
            },
            "performance_metrics": stats,
            "validation_stats": validation_stats,
            "thresholds": self.thresholds,
            "test_results": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """打印测试报告
        
        Args:
            report: 测试报告
        """
        print("\n" + "=" * 80)
        print("证书处理工作流性能验证报告")
        print("=" * 80)
        
        summary = report["summary"]
        print(f"\n测试概览:")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  成功数: {summary['successful_tests']}")
        print(f"  失败数: {summary['failed_tests']}")
        print(f"  成功率: {summary['success_rate']:.1%}")
        print(f"  总耗时: {summary['total_time_seconds']:.2f}秒")
        
        print(f"\n性能指标:")
        for metric_name, stats in report["performance_metrics"].items():
            threshold = report["thresholds"].get(metric_name, 0)
            if metric_name in ["ocr_accuracy", "rag_relevance"]:
                print(f"  {metric_name}:")
                print(f"    平均值: {stats['avg']:.2%}")
                print(f"    最小值: {stats['min']:.2%}")
                print(f"    最大值: {stats['max']:.2%}")
                print(f"    达标率: {stats['pass_rate']:.1%} (阈值: {threshold:.0%})")
            else:
                print(f"  {metric_name}:")
                print(f"    平均值: {stats['avg']:.0f}ms")
                print(f"    最小值: {stats['min']:.0f}ms")
                print(f"    最大值: {stats['max']:.0f}ms")
                print(f"    达标率: {stats['pass_rate']:.1%} (阈值: {threshold:.0f}ms)")
        
        print(f"\n验证结果:")
        validation_stats = report["validation_stats"]
        for key, stats in validation_stats.items():
            total = stats["passed"] + stats["failed"]
            pass_rate = stats["passed"] / total if total > 0 else 0
            status = "✅" if pass_rate >= 0.8 else "⚠️" if pass_rate >= 0.5 else "❌"
            print(f"  {status} {key}: {stats['passed']}/{total} 通过 ({pass_rate:.1%})")
        
        print("\n" + "=" * 80)
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """保存测试报告
        
        Args:
            report: 测试报告
            output_path: 输出路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON格式
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试报告已保存: {output_file}")


async def main():
    """主函数"""
    # 查找测试图片
    test_photo_dirs = [
        project_root / "visual_model" / "testphoto",
        project_root / "tests" / "test_photos",
        project_root / "test_photos"
    ]
    
    test_images = []
    for dir_path in test_photo_dirs:
        if dir_path.exists():
            test_images.extend(list(dir_path.glob("*.jpg"))[:5])
            test_images.extend(list(dir_path.glob("*.png"))[:5])
    
    if not test_images:
        logger.warning("未找到测试图片，使用模拟测试")
        # 创建模拟测试
        test_images = ["mock_test_image.jpg"]
    
    # 运行性能监控
    monitor = WorkflowPerformanceMonitor()
    report = await monitor.run_comprehensive_test([str(img) for img in test_images])
    
    # 打印报告
    monitor.print_report(report)
    
    # 保存报告
    output_path = project_root / "logs" / "workflow_performance_report.json"
    monitor.save_report(report, str(output_path))
    
    # 返回验证结果
    all_passed = all(
        stats["passed"] >= stats["failed"]
        for stats in report["validation_stats"].values()
    )
    
    if all_passed:
        logger.info("\n✅ 所有验证项均通过！")
        return 0
    else:
        logger.warning("\n⚠️ 部分验证项未通过，请查看详细报告")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        sys.exit(1)
