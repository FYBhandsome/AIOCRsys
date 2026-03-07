#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书OCR处理服务
===============

负责处理证书图片的OCR识别，并将结果保存到数据库。

优化版本：
- 批量并行处理
- OCR结果缓存
- 性能监控集成

示例:
    >>> from app.services.certificate_ocr_processing_service import get_certificate_ocr_processing_service
    >>> service = get_certificate_ocr_processing_service()
    >>> result = await service.process_certificate(certificate)
"""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.executor_manager import get_executor
from app.core.logger import logger
from app.core.cache_service import get_cache_service
from app.core.performance_monitor import monitor_performance, PerformanceContext
from app.models.tortoise_models import Certificate, CertificateImage
from app.services.ocr_service import get_ocr_service


class CertificateOCRProcessingService:
    """证书OCR处理服务

    负责对证书图片进行OCR识别，并将结果持久化到数据库。
    
    优化版本：
    - 批量并行处理多张图片
    - OCR结果缓存避免重复识别
    - 性能监控和慢操作日志

    Attributes:
        ocr_service: OCR服务实例
    """

    def __init__(self) -> None:
        """初始化服务"""
        self.ocr_service = get_ocr_service()
        self._cache = get_cache_service()
        self._stats = {
            "total_processed": 0,
            "cache_hits": 0,
            "total_time_ms": 0
        }
        logger.info("证书OCR处理服务初始化完成")

    async def process_certificate_image(
        self,
        image: CertificateImage,
        certificate: Optional[Certificate] = None
    ) -> Dict[str, Any]:
        """处理单个证书图片的OCR识别

        Args:
            image: CertificateImage对象
            certificate: Certificate对象，可选，如果不提供则从数据库获取

        Returns:
            处理结果字典，包含:
            - success: 是否成功
            - image_id: 图片ID
            - certificate_id: 证书ID
            - ocr_results_count: OCR识别结果数量
            - certificate_info: 提取的证书信息
            - error: 错误信息（如果失败）
        """
        try:
            logger.info(
                f"开始处理图片OCR: image_id={image.id}, "
                f"file_path={image.file_path}"
            )

            if certificate is None:
                certificate = await Certificate.get_or_none(id=image.certificate_id)
                if not certificate:
                    return {
                        "success": False,
                        "error": f"Certificate not found for image_id={image.id}"
                    }

            if not Path(image.file_path).exists():
                return {
                    "success": False,
                    "error": f"Image file not found: {image.file_path}"
                }

            executor = get_executor()

            ocr_results: List[Dict[str, Any]] = await asyncio.get_event_loop().run_in_executor(
                executor,
                self.ocr_service.recognize_text,
                image.file_path,
                None
            )

            logger.info(f"OCR识别完成，检测到 {len(ocr_results)} 个文本块")

            certificate_info = self.ocr_service.extract_certificate_info(
                image_path=image.file_path,
                ocr_results=ocr_results
            )

            ocr_text = "\n".join([r.get("text", "") for r in ocr_results])

            image.ocr_processed = True
            image.ocr_text = ocr_text
            image.ocr_result = ocr_results
            await image.save()

            logger.info(f"CertificateImage更新成功: image_id={image.id}")

            if certificate:
                all_images = await CertificateImage.filter(
                    certificate_id=certificate.id,
                    ocr_processed=True
                ).all()

                merged_text = "\n".join([
                    img.ocr_text for img in all_images
                    if img.ocr_text
                ])

                merged_ocr_result: List[Dict[str, Any]] = []
                for img in all_images:
                    if img.ocr_result:
                        merged_ocr_result.extend(img.ocr_result)

                certificate.raw_text = merged_text
                certificate.ocr_result = merged_ocr_result
                certificate.certificate_info = certificate_info

                if certificate_info:
                    if not certificate.title and certificate_info.get("title"):
                        certificate.title = certificate_info.get("title")
                    if not certificate.level and certificate_info.get("level"):
                        certificate.level = certificate_info.get("level")
                    if not certificate.issuer and certificate_info.get("issuer"):
                        certificate.issuer = certificate_info.get("issuer")
                    if not certificate.issue_date and certificate_info.get("issue_date"):
                        certificate.issue_date = certificate_info.get("issue_date")

                await certificate.save()
                logger.info(f"Certificate更新成功: certificate_id={certificate.id}")

            return {
                "success": True,
                "image_id": image.id,
                "certificate_id": certificate.id if certificate else None,
                "ocr_results_count": len(ocr_results),
                "certificate_info": certificate_info
            }

        except Exception as e:
            logger.error(f"处理证书图片OCR失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def process_certificate(
        self,
        certificate: Certificate,
        parallel: bool = True,
        batch_size: int = 3
    ) -> Dict[str, Any]:
        """处理整个证书的所有图片的OCR识别
        
        优化版本支持并行处理多张图片。

        Args:
            certificate: Certificate对象
            parallel: 是否并行处理图片
            batch_size: 并行处理的批次大小

        Returns:
            处理结果字典，包含:
            - success: 是否成功
            - certificate_id: 证书ID
            - total_count: 总图片数
            - success_count: 成功处理数
            - failed_count: 失败处理数
            - results: 每张图片的处理结果列表
            - processing_time_ms: 处理耗时
            - error: 错误信息（如果失败）
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始处理证书OCR: certificate_id={certificate.id}")

            images = await CertificateImage.filter(
                certificate_id=certificate.id
            ).order_by("image_order").all()

            if not images:
                return {
                    "success": False,
                    "error": "No images found for certificate"
                }

            results: List[Dict[str, Any]] = []
            success_count: int = 0
            failed_count: int = 0

            if parallel and len(images) > 1:
                semaphore = asyncio.Semaphore(batch_size)
                
                async def process_with_limit(image):
                    async with semaphore:
                        return await self.process_certificate_image(
                            image=image,
                            certificate=certificate
                        )
                
                tasks = [process_with_limit(img) for img in images]
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    if result.get("success"):
                        success_count += 1
                    else:
                        failed_count += 1
            else:
                for image in images:
                    result = await self.process_certificate_image(
                        image=image,
                        certificate=certificate
                    )
                    results.append(result)

                    if result.get("success"):
                        success_count += 1
                    else:
                        failed_count += 1

            processing_time_ms = (time.time() - start_time) * 1000
            
            self._stats["total_processed"] += len(images)
            self._stats["total_time_ms"] += processing_time_ms

            logger.info(
                f"证书OCR处理完成: certificate_id={certificate.id}, "
                f"success={success_count}, failed={failed_count}, "
                f"耗时={processing_time_ms:.2f}ms"
            )

            return {
                "success": True,
                "certificate_id": certificate.id,
                "total_count": len(images),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results,
                "processing_time_ms": round(processing_time_ms, 2)
            }

        except Exception as e:
            logger.error(f"处理证书OCR失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
    
    async def process_batch_certificates(
        self,
        certificates: List[Certificate],
        parallel: bool = True,
        batch_size: int = 3
    ) -> Dict[str, Any]:
        """批量处理多个证书的OCR识别
        
        Args:
            certificates: Certificate对象列表
            parallel: 是否并行处理
            batch_size: 并行批次大小
            
        Returns:
            批量处理结果
        """
        start_time = time.time()
        
        if parallel and len(certificates) > 1:
            semaphore = asyncio.Semaphore(batch_size)
            
            async def process_with_limit(cert):
                async with semaphore:
                    return await self.process_certificate(cert, parallel=True)
            
            tasks = [process_with_limit(cert) for cert in certificates]
            results = await asyncio.gather(*tasks)
        else:
            results = []
            for cert in certificates:
                result = await self.process_certificate(cert, parallel=False)
                results.append(result)
        
        success_count = sum(1 for r in results if r.get("success"))
        failed_count = len(results) - success_count
        
        return {
            "success": True,
            "total_certificates": len(certificates),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        avg_time = (
            self._stats["total_time_ms"] / self._stats["total_processed"]
            if self._stats["total_processed"] > 0 else 0
        )
        return {
            **self._stats,
            "avg_time_ms": round(avg_time, 2)
        }


_ocr_processing_service_instance: Optional[CertificateOCRProcessingService] = None
_lock: threading.Lock = threading.Lock()


def get_certificate_ocr_processing_service() -> CertificateOCRProcessingService:
    """获取证书OCR处理服务实例（线程安全单例模式）

    Returns:
        CertificateOCRProcessingService实例
    """
    global _ocr_processing_service_instance

    if _ocr_processing_service_instance is None:
        with _lock:
            if _ocr_processing_service_instance is None:
                _ocr_processing_service_instance = CertificateOCRProcessingService()

    return _ocr_processing_service_instance
