#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获奖证书OCR识别业务逻辑

处理获奖证书图片的OCR识别和信息提取。
"""

import json
from typing import Dict, Any
from pathlib import Path

from app.core.logger import logger
from app.services.ocr_service import get_ocr_service
from app.services.image_service import get_image_service
from config import settings


class CertificateOCRService:
    """获奖证书OCR识别服务"""
    
    def __init__(self):
        """初始化获奖证书OCR服务"""
        self.ocr_service = get_ocr_service()
        self.image_service = get_image_service()
        logger.info("获奖证书OCR服务初始化完成")
    
    def process_certificate_image(self, image_path: str) -> Dict[str, Any]:
        """处理获奖证书图片，进行OCR识别并提取关键信息
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            包含识别结果的字典
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # OCR识别（直接识别，不预处理）
            ocr_results = self.ocr_service.recognize_text(image_path)
            
            # 提取证书信息
            certificate_info = self.ocr_service.extract_certificate_info(
                image_path,
                ocr_results=ocr_results
            )
            
            # 保存识别结果
            self._save_result(image_path, ocr_results, certificate_info)
            
            return {
                "success": True,
                "image_path": image_path,
                "ocr_results": ocr_results,
                "certificate_info": certificate_info
            }
            
        except Exception as e:
            logger.error(f"处理获奖证书图片失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "image_path": image_path
            }
    
    def _save_result(self, image_path: str, ocr_results: list, 
                    certificate_info: Dict[str, Any]) -> None:
        """保存OCR识别结果到文件"""
        try:
            # 创建结果目录
            results_dir = Path(settings.RESULT_DIR)
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成结果文件名
            image_name = Path(image_path).stem
            result_file = results_dir / f"{image_name}_ocr_result.json"
            
            # 保存数据
            save_data = {
                "image_path": image_path,
                "ocr_results": ocr_results,
                "certificate_info": certificate_info
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"OCR识别结果已保存到: {result_file}")
            
        except Exception as e:
            logger.error(f"保存OCR识别结果失败: {e}", exc_info=True)
