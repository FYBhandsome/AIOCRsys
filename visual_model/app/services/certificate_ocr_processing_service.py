#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书OCR处理服务
负责处理证书图片的OCR识别，并将结果保存到数据库
"""
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.logger import logger
from app.core.executor_manager import get_executor
from app.services.ocr_service import get_ocr_service
from app.models.tortoise_models import Certificate, CertificateImage


class CertificateOCRProcessingService:
    """证书OCR处理服务"""
    
    def __init__(self):
        """初始化服务"""
        self.ocr_service = get_ocr_service()
        self.executor = get_executor()
        logger.info("证书OCR处理服务初始化完成")
    
    async def process_certificate_image(
        self,
        image: CertificateImage,
        certificate: Optional[Certificate] = None
    ) -> Dict[str, Any]:
        """处理单个证书图片的OCR识别
        
        Args:
            image: CertificateImage对象
            certificate: Certificate对象（可选，如果不提供则从数据库获取）
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理图片OCR: image_id={image.id}, file_path={image.file_path}")
            
            # 获取certificate对象
            if certificate is None:
                certificate = await Certificate.get_or_none(id=image.certificate_id)
                if not certificate:
                    return {
                        "success": False,
                        "error": f"Certificate not found for image_id={image.id}"
                    }
            
            # 检查文件是否存在
            if not Path(image.file_path).exists():
                return {
                    "success": False,
                    "error": f"Image file not found: {image.file_path}"
                }
            
            # 在线程池中执行OCR识别（避免阻塞事件循环）
            ocr_results = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.ocr_service.recognize_text,
                image.file_path,
                None
            )
            
            logger.info(f"OCR识别完成，检测到 {len(ocr_results)} 个文本块")
            
            # 提取证书信息
            certificate_info = self.ocr_service.extract_certificate_info(
                image_path=image.file_path,
                ocr_results=ocr_results
            )
            
            # 准备OCR文本
            ocr_text = "\n".join([r.get("text", "") for r in ocr_results])
            
            # 更新CertificateImage
            image.ocr_processed = True
            image.ocr_text = ocr_text
            image.ocr_result = ocr_results
            await image.save()
            
            logger.info(f"CertificateImage更新成功: image_id={image.id}")
            
            # 更新Certificate
            if certificate:
                # 合并所有图片的OCR文本（如果有多个图片）
                all_images = await CertificateImage.filter(
                    certificate_id=certificate.id,
                    ocr_processed=True
                ).all()
                
                merged_text = "\n".join([
                    img.ocr_text for img in all_images 
                    if img.ocr_text
                ])
                
                # 合并所有图片的OCR结果
                merged_ocr_result = []
                for img in all_images:
                    if img.ocr_result:
                        merged_ocr_result.extend(img.ocr_result)
                
                # 更新Certificate
                certificate.raw_text = merged_text
                certificate.ocr_result = merged_ocr_result
                certificate.certificate_info = certificate_info
                
                # 尝试填充基本字段
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
        certificate: Certificate
    ) -> Dict[str, Any]:
        """处理整个证书的所有图片的OCR识别
        
        Args:
            certificate: Certificate对象
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理证书OCR: certificate_id={certificate.id}")
            
            # 获取所有图片
            images = await CertificateImage.filter(
                certificate_id=certificate.id
            ).order_by("image_order").all()
            
            if not images:
                return {
                    "success": False,
                    "error": "No images found for certificate"
                }
            
            results = []
            success_count = 0
            failed_count = 0
            
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
            
            logger.info(
                f"证书OCR处理完成: certificate_id={certificate.id}, "
                f"success={success_count}, failed={failed_count}"
            )
            
            return {
                "success": True,
                "certificate_id": certificate.id,
                "total_count": len(images),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"处理证书OCR失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# 全局单例
_ocr_processing_service_instance: Optional[CertificateOCRProcessingService] = None


def get_certificate_ocr_processing_service() -> CertificateOCRProcessingService:
    """获取证书OCR处理服务实例（单例模式）"""
    global _ocr_processing_service_instance
    
    if _ocr_processing_service_instance is None:
        _ocr_processing_service_instance = CertificateOCRProcessingService()
    
    return _ocr_processing_service_instance
