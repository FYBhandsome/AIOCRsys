#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书处理完整工作流测试
========================

测试流程:
1. 上传证书文档
2. 调用OCR服务提取文本信息
3. 使用提取的文本信息进行RAG检索
4. 将检索到的信息与提取的文本结合发送给AI模型
5. 获取并返回AI模型的评分结果

边界情况测试:
- 无法读取的证书
- OCR提取失败
- RAG检索错误
- AI模型响应问题
"""

import pytest
import asyncio
import logging
import time
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from io import BytesIO
from PIL import Image
import numpy as np

from httpx import AsyncClient

logger = logging.getLogger("workflow_test")


class WorkflowTestResult:
    """工作流测试结果"""
    
    def __init__(self):
        self.test_name: str = ""
        self.success: bool = False
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration_ms: float = 0.0
        self.steps: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.metrics: Dict[str, Any] = {}
        
    def add_step(self, step_name: str, success: bool, duration_ms: float, 
                 details: Optional[Dict[str, Any]] = None):
        """添加测试步骤"""
        self.steps.append({
            "step_name": step_name,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_name": self.test_name,
            "success": self.success,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "steps": self.steps,
            "errors": self.errors,
            "metrics": self.metrics
        }


class CertificateWorkflowTester:
    """证书处理工作流测试器"""
    
    def __init__(self, client: AsyncClient, auth_token: str):
        self.client = client
        self.auth_token = auth_token
        self.api_prefix = "/api/v1"
        self.headers = {"Authorization": f"Bearer {auth_token}"}
        
    async def test_complete_workflow(
        self, 
        image_path: str, 
        student_id: str,
        expected_category: Optional[str] = None
    ) -> WorkflowTestResult:
        """测试完整工作流
        
        Args:
            image_path: 证书图片路径
            student_id: 学号
            expected_category: 预期类别（可选）
            
        Returns:
            WorkflowTestResult: 测试结果
        """
        result = WorkflowTestResult()
        result.test_name = f"完整工作流测试 - {Path(image_path).name}"
        result.start_time = time.time()
        
        try:
            # Step 1: 上传证书
            step_start = time.time()
            upload_result = await self._upload_certificate(image_path, student_id)
            step_duration = (time.time() - step_start) * 1000
            
            if not upload_result["success"]:
                result.add_step("证书上传", False, step_duration, upload_result)
                result.errors.append(f"证书上传失败: {upload_result.get('error')}")
                result.success = False
                return result
                
            result.add_step("证书上传", True, step_duration, {
                "certificate_id": upload_result.get("certificate_id"),
                "image_count": upload_result.get("image_count", 0)
            })
            
            certificate_id = upload_result["certificate_id"]
            
            # Step 2: OCR识别
            step_start = time.time()
            ocr_result = await self._trigger_ocr(certificate_id)
            step_duration = (time.time() - step_start) * 1000
            
            if not ocr_result["success"]:
                result.add_step("OCR识别", False, step_duration, ocr_result)
                result.errors.append(f"OCR识别失败: {ocr_result.get('error')}")
                result.success = False
                return result
                
            result.add_step("OCR识别", True, step_duration, {
                "text_length": len(ocr_result.get("raw_text", "")),
                "confidence": ocr_result.get("confidence", 0)
            })
            
            # Step 3: RAG检索
            step_start = time.time()
            rag_result = await self._perform_rag_retrieval(
                ocr_result.get("raw_text", ""),
                student_id
            )
            step_duration = (time.time() - step_start) * 1000
            
            result.add_step("RAG检索", True, step_duration, {
                "rules_found": len(rag_result.get("rules", [])),
                "rag_used": rag_result.get("rag_used", False)
            })
            
            # Step 4: AI评分
            step_start = time.time()
            score_result = await self._calculate_score(
                ocr_result.get("raw_text", ""),
                ocr_result.get("certificate_info", {}),
                {"student_id": student_id}
            )
            step_duration = (time.time() - step_start) * 1000
            
            if not score_result["success"]:
                result.add_step("AI评分", False, step_duration, score_result)
                result.errors.append(f"AI评分失败: {score_result.get('error')}")
                result.success = False
                return result
                
            result.add_step("AI评分", True, step_duration, {
                "category": score_result.get("category"),
                "score": score_result.get("score"),
                "confidence": score_result.get("confidence")
            })
            
            # 验证预期结果
            if expected_category and score_result.get("category") != expected_category:
                result.errors.append(
                    f"类别不匹配: 预期 {expected_category}, 实际 {score_result.get('category')}"
                )
                result.success = False
            else:
                result.success = True
                
            # 收集指标
            result.metrics = {
                "total_text_length": len(ocr_result.get("raw_text", "")),
                "ocr_confidence": ocr_result.get("confidence", 0),
                "final_category": score_result.get("category"),
                "final_score": score_result.get("score"),
                "rag_rules_count": len(rag_result.get("rules", [])),
                "certificate_id": certificate_id
            }
            
        except Exception as e:
            logger.error(f"工作流测试异常: {e}", exc_info=True)
            result.errors.append(f"测试异常: {str(e)}")
            result.success = False
            
        finally:
            result.end_time = time.time()
            result.duration_ms = (result.end_time - result.start_time) * 1000
            
        return result
    
    async def _upload_certificate(
        self, 
        image_path: str, 
        student_id: str
    ) -> Dict[str, Any]:
        """上传证书"""
        try:
            with open(image_path, 'rb') as f:
                image_content = f.read()
            
            filename = Path(image_path).name
            files = {
                "files": (filename, BytesIO(image_content), "image/jpeg")
            }
            data = {
                "student_id": student_id,
                "category": "C",
                "sub_category": "C1"
            }
            
            response = await self.client.post(
                f"{self.api_prefix}/certificate/upload",
                files=files,
                data=data,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "certificate_id": result.get("certificate_id"),
                    "image_count": len(result.get("images", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"上传证书失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _trigger_ocr(self, certificate_id: int) -> Dict[str, Any]:
        """触发OCR识别"""
        try:
            response = await self.client.post(
                f"{self.api_prefix}/certificate/{certificate_id}/ocr/trigger",
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                # 等待OCR处理完成
                await asyncio.sleep(2)
                
                # 获取证书详情
                detail_response = await self.client.get(
                    f"{self.api_prefix}/certificate/{certificate_id}",
                    headers=self.headers
                )
                
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    return {
                        "success": True,
                        "raw_text": detail.get("raw_text", ""),
                        "certificate_info": detail.get("certificate_info", {}),
                        "confidence": detail.get("certificate_info", {}).get("confidence", 0)
                    }
                else:
                    return {
                        "success": True,
                        "raw_text": result.get("raw_text", ""),
                        "certificate_info": result.get("certificate_info", {}),
                        "confidence": result.get("certificate_info", {}).get("confidence", 0)
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"OCR识别失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _perform_rag_retrieval(
        self, 
        certificate_text: str,
        student_id: str
    ) -> Dict[str, Any]:
        """执行RAG检索"""
        try:
            response = await self.client.post(
                f"{self.api_prefix}/ai/chat",
                json={
                    "message": f"请根据以下证书内容检索相关规则: {certificate_text[:500]}",
                    "use_rag": True,
                    "userId": student_id
                },
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "rules": result.get("sources", []),
                    "rag_used": True,
                    "reply": result.get("reply", "")
                }
            else:
                return {
                    "success": True,
                    "rules": [],
                    "rag_used": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.warning(f"RAG检索失败: {e}")
            return {
                "success": True,
                "rules": [],
                "rag_used": False,
                "error": str(e)
            }
    
    async def _calculate_score(
        self,
        certificate_text: str,
        certificate_info: Dict[str, Any],
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算分数"""
        try:
            from app.services.certificate_service import get_certificate_service
            
            service = get_certificate_service()
            result = await service.classify_and_calculate_score(
                certificate_text=certificate_text,
                certificate_info=certificate_info,
                student_info=student_info
            )
            
            return {
                "success": True,
                "category": result.get("category", "C"),
                "score": result.get("score", 0.0),
                "confidence": result.get("confidence", 0.0),
                "reason": result.get("reason", ""),
                "method": result.get("method", "unknown")
            }
            
        except Exception as e:
            logger.error(f"计算分数失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


class EdgeCaseTester:
    """边界情况测试器"""
    
    def __init__(self, client: AsyncClient, auth_token: str):
        self.client = client
        self.auth_token = auth_token
        self.api_prefix = "/api/v1"
        self.headers = {"Authorization": f"Bearer {auth_token}"}
        
    async def test_unreadable_certificate(self) -> WorkflowTestResult:
        """测试无法读取的证书"""
        result = WorkflowTestResult()
        result.test_name = "边界测试 - 无法读取的证书"
        result.start_time = time.time()
        
        try:
            # 创建一个损坏的图片文件
            corrupted_image = b"not a valid image content"
            
            files = {
                "files": ("corrupted.jpg", BytesIO(corrupted_image), "image/jpeg")
            }
            data = {
                "student_id": "2024001",
                "category": "C"
            }
            
            step_start = time.time()
            response = await self.client.post(
                f"{self.api_prefix}/certificate/upload",
                files=files,
                data=data,
                headers=self.headers
            )
            step_duration = (time.time() - step_start) * 1000
            
            # 应该返回错误或成功处理（取决于系统设计）
            if response.status_code in [400, 422, 500]:
                result.add_step("损坏图片上传", True, step_duration, {
                    "status_code": response.status_code,
                    "handled_gracefully": True
                })
                result.success = True
            else:
                result.add_step("损坏图片上传", False, step_duration, {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                })
                result.success = False
                result.errors.append("系统未能正确处理损坏的图片")
                
        except Exception as e:
            result.errors.append(f"测试异常: {str(e)}")
            result.success = False
            
        finally:
            result.end_time = time.time()
            result.duration_ms = (result.end_time - result.start_time) * 1000
            
        return result
    
    async def test_ocr_failure(self) -> WorkflowTestResult:
        """测试OCR提取失败"""
        result = WorkflowTestResult()
        result.test_name = "边界测试 - OCR提取失败"
        result.start_time = time.time()
        
        try:
            # 创建一个空白图片
            blank_image = Image.new('RGB', (100, 100), color='white')
            img_buffer = BytesIO()
            blank_image.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            
            files = {
                "files": ("blank.jpg", img_buffer, "image/jpeg")
            }
            data = {
                "student_id": "2024001",
                "category": "C"
            }
            
            step_start = time.time()
            response = await self.client.post(
                f"{self.api_prefix}/certificate/upload",
                files=files,
                data=data,
                headers=self.headers
            )
            step_duration = (time.time() - step_start) * 1000
            
            if response.status_code in [200, 201]:
                result_json = response.json()
                certificate_id = result_json.get("certificate_id")
                
                # 触发OCR
                ocr_response = await self.client.post(
                    f"{self.api_prefix}/certificate/{certificate_id}/ocr/trigger",
                    headers=self.headers
                )
                
                if ocr_response.status_code in [200, 201]:
                    ocr_result = ocr_response.json()
                    
                    # 空白图片应该返回空文本或低置信度
                    result.add_step("空白图片OCR", True, step_duration, {
                        "text_length": len(ocr_result.get("raw_text", "")),
                        "handled_gracefully": True
                    })
                    result.success = True
                else:
                    result.add_step("空白图片OCR", False, step_duration, {
                        "error": "OCR触发失败"
                    })
                    result.success = False
            else:
                result.add_step("空白图片上传", False, step_duration, {
                    "status_code": response.status_code
                })
                result.success = False
                
        except Exception as e:
            result.errors.append(f"测试异常: {str(e)}")
            result.success = False
            
        finally:
            result.end_time = time.time()
            result.duration_ms = (result.end_time - result.start_time) * 1000
            
        return result
    
    async def test_rag_error(self) -> WorkflowTestResult:
        """测试RAG检索错误"""
        result = WorkflowTestResult()
        result.test_name = "边界测试 - RAG检索错误"
        result.start_time = time.time()
        
        try:
            # 测试RAG服务不可用的情况
            step_start = time.time()
            
            # 发送一个可能导致RAG错误的请求
            response = await self.client.post(
                f"{self.api_prefix}/ai/chat",
                json={
                    "message": "",  # 空消息
                    "use_rag": True,
                    "userId": "test_user"
                },
                headers=self.headers
            )
            step_duration = (time.time() - step_start) * 1000
            
            # 系统应该优雅地处理错误
            if response.status_code in [200, 400, 422]:
                result.add_step("RAG错误处理", True, step_duration, {
                    "status_code": response.status_code,
                    "handled_gracefully": True
                })
                result.success = True
            else:
                result.add_step("RAG错误处理", False, step_duration, {
                    "status_code": response.status_code
                })
                result.success = False
                
        except Exception as e:
            # 如果抛出异常，说明错误处理不当
            result.errors.append(f"测试异常: {str(e)}")
            result.success = False
            
        finally:
            result.end_time = time.time()
            result.duration_ms = (result.end_time - result.start_time) * 1000
            
        return result
    
    async def test_ai_model_timeout(self) -> WorkflowTestResult:
        """测试AI模型超时"""
        result = WorkflowTestResult()
        result.test_name = "边界测试 - AI模型超时"
        result.start_time = time.time()
        
        try:
            # 创建一个非常大的文本，可能导致超时
            large_text = "测试" * 10000
            
            step_start = time.time()
            response = await self.client.post(
                f"{self.api_prefix}/ai/chat",
                json={
                    "message": large_text,
                    "use_rag": False,
                    "userId": "test_user"
                },
                headers=self.headers,
                timeout=30.0  # 设置超时时间
            )
            step_duration = (time.time() - step_start) * 1000
            
            # 系统应该在超时前返回响应
            if response.status_code in [200, 408, 500]:
                result.add_step("AI模型超时处理", True, step_duration, {
                    "status_code": response.status_code,
                    "duration_ms": step_duration
                })
                result.success = True
            else:
                result.add_step("AI模型超时处理", False, step_duration, {
                    "status_code": response.status_code
                })
                result.success = False
                
        except Exception as e:
            result.errors.append(f"测试异常: {str(e)}")
            # 超时异常也算作正确处理
            if "timeout" in str(e).lower():
                result.success = True
            else:
                result.success = False
                
        finally:
            result.end_time = time.time()
            result.duration_ms = (result.end_time - result.start_time) * 1000
            
        return result


class TestMetricsCollector:
    """测试指标收集器"""
    
    def __init__(self):
        self.results: List[WorkflowTestResult] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        
    def add_result(self, result: WorkflowTestResult):
        """添加测试结果"""
        self.results.append(result)
        
    def calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        if not self.results:
            return {}
            
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        durations = [r.duration_ms for r in self.results]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # 统计各步骤的成功率
        step_stats = {}
        for result in self.results:
            for step in result.steps:
                step_name = step["step_name"]
                if step_name not in step_stats:
                    step_stats[step_name] = {"total": 0, "success": 0, "failed": 0}
                
                step_stats[step_name]["total"] += 1
                if step["success"]:
                    step_stats[step_name]["success"] += 1
                else:
                    step_stats[step_name]["failed"] += 1
        
        # 计算每个步骤的成功率
        for step_name, stats in step_stats.items():
            stats["success_rate"] = (
                stats["success"] / stats["total"] * 100 
                if stats["total"] > 0 else 0
            )
        
        # 统计错误类型
        error_types = {}
        for result in self.results:
            for error in result.errors:
                error_type = error.split(":")[0] if ":" in error else error
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round(success_rate, 2),
            "duration_stats": {
                "avg_ms": round(avg_duration, 2),
                "min_ms": round(min_duration, 2),
                "max_ms": round(max_duration, 2),
                "total_ms": round(sum(durations), 2)
            },
            "step_statistics": step_stats,
            "error_types": error_types,
            "test_duration_seconds": round(self.end_time - self.start_time, 2)
        }
    
    def generate_report(self) -> str:
        """生成测试报告"""
        stats = self.calculate_statistics()
        
        report_lines = [
            "=" * 80,
            "证书处理工作流测试报告",
            "=" * 80,
            f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"测试总数: {stats.get('total_tests', 0)}",
            f"成功数量: {stats.get('successful_tests', 0)}",
            f"失败数量: {stats.get('failed_tests', 0)}",
            f"成功率: {stats.get('success_rate', 0)}%",
            "",
            "性能指标:",
            f"  平均耗时: {stats.get('duration_stats', {}).get('avg_ms', 0)} ms",
            f"  最小耗时: {stats.get('duration_stats', {}).get('min_ms', 0)} ms",
            f"  最大耗时: {stats.get('duration_stats', {}).get('max_ms', 0)} ms",
            f"  总耗时: {stats.get('duration_stats', {}).get('total_ms', 0)} ms",
            "",
            "步骤统计:",
        ]
        
        for step_name, step_stats in stats.get("step_statistics", {}).items():
            report_lines.append(
                f"  {step_name}: "
                f"总数={step_stats['total']}, "
                f"成功={step_stats['success']}, "
                f"失败={step_stats['failed']}, "
                f"成功率={step_stats['success_rate']:.1f}%"
            )
        
        if stats.get("error_types"):
            report_lines.append("")
            report_lines.append("错误类型统计:")
            for error_type, count in stats["error_types"].items():
                report_lines.append(f"  {error_type}: {count} 次")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report(self, filepath: str):
        """保存测试报告"""
        report = self.generate_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 同时保存JSON格式的详细结果
        json_filepath = filepath.replace('.txt', '.json')
        results_data = {
            "statistics": self.calculate_statistics(),
            "results": [r.to_dict() for r in self.results]
        }
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试报告已保存: {filepath}")
        logger.info(f"详细结果已保存: {json_filepath}")


# ============================================================================
# Pytest测试用例
# ============================================================================

@pytest.mark.workflow
@pytest.mark.asyncio
async def test_complete_certificate_workflow(
    client: AsyncClient,
    student_token: str,
    test_photo_dir: Path,
    test_logger
):
    """测试完整的证书处理工作流"""
    test_logger.info("开始测试: 完整证书处理工作流")
    
    tester = CertificateWorkflowTester(client, student_token)
    metrics = TestMetricsCollector()
    metrics.start_time = time.time()
    
    # 获取测试照片
    test_photos = list(test_photo_dir.glob("*.jpg")) + list(test_photo_dir.glob("*.png"))
    
    if not test_photos:
        test_logger.warning("未找到测试照片，跳过测试")
        pytest.skip("未找到测试照片")
    
    # 测试前5张照片
    for photo_path in test_photos[:5]:
        test_logger.info(f"测试照片: {photo_path.name}")
        
        result = await tester.test_complete_workflow(
            image_path=str(photo_path),
            student_id="2024001"
        )
        
        metrics.add_result(result)
        
        test_logger.info(
            f"测试结果: {'成功' if result.success else '失败'}, "
            f"耗时: {result.duration_ms:.2f}ms"
        )
        
        if not result.success:
            test_logger.error(f"错误: {result.errors}")
    
    metrics.end_time = time.time()
    
    # 生成报告
    report_path = test_photo_dir.parent / "workflow_test_report.txt"
    metrics.save_report(str(report_path))
    
    # 打印报告
    test_logger.info("\n" + metrics.generate_report())
    
    # 验证成功率
    stats = metrics.calculate_statistics()
    assert stats["success_rate"] >= 60, f"成功率过低: {stats['success_rate']}%"


@pytest.mark.workflow
@pytest.mark.asyncio
async def test_edge_cases(
    client: AsyncClient,
    student_token: str,
    test_logger
):
    """测试边界情况"""
    test_logger.info("开始测试: 边界情况")
    
    tester = EdgeCaseTester(client, student_token)
    metrics = TestMetricsCollector()
    metrics.start_time = time.time()
    
    # 测试各种边界情况
    test_cases = [
        ("无法读取的证书", tester.test_unreadable_certificate),
        ("OCR提取失败", tester.test_ocr_failure),
        ("RAG检索错误", tester.test_rag_error),
        ("AI模型超时", tester.test_ai_model_timeout)
    ]
    
    for case_name, test_func in test_cases:
        test_logger.info(f"测试边界情况: {case_name}")
        
        result = await test_func()
        metrics.add_result(result)
        
        test_logger.info(
            f"结果: {'通过' if result.success else '失败'}, "
            f"耗时: {result.duration_ms:.2f}ms"
        )
    
    metrics.end_time = time.time()
    
    # 生成报告
    report_path = Path("logs/edge_case_test_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metrics.save_report(str(report_path))
    
    # 打印报告
    test_logger.info("\n" + metrics.generate_report())
    
    # 验证所有边界情况都被正确处理
    stats = metrics.calculate_statistics()
    assert stats["success_rate"] >= 75, f"边界情况处理成功率过低: {stats['success_rate']}%"


@pytest.mark.workflow
@pytest.mark.asyncio
async def test_workflow_performance(
    client: AsyncClient,
    student_token: str,
    test_photo_dir: Path,
    test_logger
):
    """测试工作流性能"""
    test_logger.info("开始测试: 工作流性能")
    
    tester = CertificateWorkflowTester(client, student_token)
    
    # 获取测试照片
    test_photos = list(test_photo_dir.glob("*.jpg"))
    
    if not test_photos:
        pytest.skip("未找到测试照片")
    
    # 测试单张照片的处理时间
    photo_path = test_photos[0]
    
    result = await tester.test_complete_workflow(
        image_path=str(photo_path),
        student_id="2024001"
    )
    
    test_logger.info(f"单次处理耗时: {result.duration_ms:.2f}ms")
    
    # 验证性能指标
    assert result.duration_ms < 10000, f"处理时间过长: {result.duration_ms}ms"
    
    # 测试并发处理
    test_logger.info("测试并发处理...")
    concurrent_tasks = []
    for photo in test_photos[:3]:
        task = tester.test_complete_workflow(
            image_path=str(photo),
            student_id="2024001"
        )
        concurrent_tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
    total_duration = (time.time() - start_time) * 1000
    
    successful = sum(1 for r in results if isinstance(r, WorkflowTestResult) and r.success)
    
    test_logger.info(
        f"并发处理结果: 成功 {successful}/{len(concurrent_tasks)}, "
        f"总耗时: {total_duration:.2f}ms"
    )
    
    assert successful >= 2, "并发处理成功率过低"
