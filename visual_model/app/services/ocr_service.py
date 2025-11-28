#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR服务封装 - 基于PaddleOCR

提供图像OCR识别和证书信息提取功能。
"""

from typing import Dict, Any, List, Union, Optional
import re
from pathlib import Path

import numpy as np
from PIL import Image

from app.core.logger import logger
from config import settings

# 导入PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLE_OCR_AVAILABLE = True
except ImportError:
    logger.warning("PaddleOCR未安装，OCR功能将不可用")
    PADDLE_OCR_AVAILABLE = False
    PaddleOCR = None  # type: ignore


class OCRService:
    """PaddleOCR服务封装
    
    负责图像文字识别和证书信息提取。
    """
    
    def __init__(self, use_gpu: bool = False, lang: str = "ch"):
        """初始化OCR服务
        
        Args:
            use_gpu: 是否使用GPU加速
            lang: 识别语言
        """
        if not PADDLE_OCR_AVAILABLE:
            raise RuntimeError("PaddleOCR未安装，无法使用OCR功能")
        
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr: Optional[PaddleOCR] = None
        logger.info("OCR服务已创建，模型将在首次使用时加载")
    
    def _initialize_ocr(self) -> None:
        """初始化PaddleOCR引擎（懒加载）"""
        if self.ocr is not None:
            return
        
        logger.info("正在初始化PaddleOCR...")
        try:
            device = "gpu:0" if self.use_gpu else "cpu"
            
            # 基本初始化参数，避免使用不兼容的参数
            init_params = {
                "lang": self.lang,
                "device": device,
                "det_db_thresh": getattr(settings, 'OCR_DET_DB_THRESH', 0.3),
                "det_db_box_thresh": getattr(settings, 'OCR_DET_DB_BOX_THRESH', 0.6),
                "rec_batch_num": getattr(settings, 'OCR_REC_BATCH_NUM', 6)
            }
            
            # 尝试添加方向分类器参数，如果失败则跳过
            try:
                if settings.OCR_USE_ANGLE_CLS:
                    init_params["use_angle_cls"] = True
                    self.ocr = PaddleOCR(**init_params)
                    logger.info(f"PaddleOCR初始化成功 (device={device}, use_angle_cls=True)")
                else:
                    self.ocr = PaddleOCR(**init_params)
                    logger.info(f"PaddleOCR初始化成功 (device={device}, use_angle_cls=False)")
            except TypeError as e:
                if "use_angle_cls" in str(e):
                    logger.warning(f"方向分类器参数不被支持: {e}，将不使用该参数重新初始化")
                    # 移除不兼容的参数
                    if "use_angle_cls" in init_params:
                        del init_params["use_angle_cls"]
                    self.ocr = PaddleOCR(**init_params)
                    logger.info(f"PaddleOCR初始化成功 (device={device}, 不使用方向分类器)")
                else:
                    raise e
            
        except Exception as e:
            logger.error(f"PaddleOCR初始化失败: {e}", exc_info=True)
            raise
    
    def warm_up(self) -> None:
        """预热OCR引擎"""
        try:
            self._initialize_ocr()
            logger.info("PaddleOCR已预热完成")
        except Exception:
            logger.warning("PaddleOCR预热失败，将在首次请求时重试", exc_info=True)
    
    def recognize_text(self, image_input: Union[str, Path, np.ndarray], 
                      threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """识别图像中的文本
        
        Args:
            image_input: 图像路径或numpy数组
            threshold: 最小置信度阈值（None则使用配置值）
            
        Returns:
            识别结果列表，每个元素包含 box, text, score
        """
        self._initialize_ocr()
        
        # 加载图像
        img_array = self._load_image(image_input)
        logger.info(f"图像加载完成，尺寸: {img_array.shape}")
        
        # OCR识别
        try:
            logger.info("开始OCR识别...")
            result = self.ocr.ocr(img_array)
            raw_count = len(result[0]) if result and result[0] else 0
            logger.info(f"OCR识别完成，检测到 {raw_count} 个文本框")
        except Exception as e:
            logger.error(f"OCR识别失败: {e}", exc_info=True)
            return []
        
        # 使用极低阈值格式化结果（先看原始分数分布）
        if not result or not result[0]:
            logger.warning("未检测到任何文本框")
            return []
        
        # 打印所有原始结果的置信度分布
        all_scores = []
        for line in result[0]:
            if line and len(line) >= 2 and line[1] and len(line[1]) >= 2:
                score = float(line[1][1])
                all_scores.append(score)
        
        if all_scores:
            logger.info(f"置信度分布: min={min(all_scores):.3f}, max={max(all_scores):.3f}, "
                       f"avg={sum(all_scores)/len(all_scores):.3f}")
        
        # 使用极低阈值（0.01）先获取所有结果
        effective_threshold = threshold if threshold is not None else settings.OCR_THRESHOLD
        min_threshold = 0.01  # 极低阈值，几乎保留所有结果
        
        all_results = self._format_results(result, min_threshold)
        logger.info(f"原始识别到 {len(all_results)} 条文本（阈值={min_threshold}）")
        
        # 打印前10条原始结果
        if all_results:
            preview_count = min(10, len(all_results))
            logger.info(f"=== 前{preview_count}条原始识别结果 ===")
            for idx in range(preview_count):
                item = all_results[idx]
                logger.info(f"  [{idx+1}] score={item['score']:.3f}, text='{item['text']}'")
        
        # 应用用户阈值过滤
        filtered_results = [r for r in all_results if r['score'] >= effective_threshold]
        logger.info(f"应用阈值 {effective_threshold} 后保留 {len(filtered_results)} 条")
        
        # 如果过滤后为空，尝试降低阈值
        if len(filtered_results) == 0 and len(all_results) > 0:
            fallback_threshold = min(0.15, max(all_scores) * 0.8) if all_scores else 0.15
            logger.warning(f"阈值 {effective_threshold} 过高，自动降低至 {fallback_threshold:.3f}")
            filtered_results = [r for r in all_results if r['score'] >= fallback_threshold]
            logger.info(f"降低阈值后保留 {len(filtered_results)} 条")
        
        return filtered_results
    
    def _load_image(self, image_input: Union[str, Path, np.ndarray]) -> np.ndarray:
        """加载图像为numpy数组"""
        if isinstance(image_input, np.ndarray):
            return image_input
        
        image_path = Path(image_input)
        if not image_path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                max_dimension = getattr(settings, 'OCR_MAX_IMAGE_SIZE', 1600)
                
                if width > max_dimension or height > max_dimension:
                    ratio = min(max_dimension / width, max_dimension / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    try:
                        resample_filter = Image.LANCZOS
                    except AttributeError:
                        resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else 1
                    img = img.resize((new_width, new_height), resample_filter)
                    logger.info(f"图像已缩放: {width}x{height} -> {new_width}x{new_height}")
                
                return np.array(img.convert('RGB'))
        except Exception as e:
            logger.error(f"读取图像失败: {e}")
            raise ValueError(f"读取图像失败: {e}")
    
    def _format_results(self, result: Any, threshold: float) -> List[Dict[str, Any]]:
        """格式化OCR识别结果"""
        formatted_results = []
        
        if not result:
            return formatted_results
        
        # 处理新版本的OCRResult对象（字典式对象）
        if hasattr(result, '__len__') and len(result) > 0 and hasattr(result[0], 'get'):
            # 新版本PaddleX格式 - OCRResult对象行为类似字典
            ocr_result = result[0]
            
            # 获取识别文本和分数
            rec_texts = ocr_result.get('rec_texts', [])
            rec_scores = ocr_result.get('rec_scores', [])
            
            # 获取文本框坐标
            boxes = ocr_result.get('dt_polys', [])
            
            logger.info(f"新版本OCRResult格式: 文本数={len(rec_texts)}, 分数数={len(rec_scores)}, 框数={len(boxes)}")
            
            # 格式化结果
            for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                if score >= threshold:
                    box = boxes[i].tolist() if i < len(boxes) and hasattr(boxes[i], 'tolist') else []
                    formatted_results.append({
                        "box": box,
                        "text": text,
                        "score": float(score)
                    })
            return formatted_results
        
        # 处理旧版本标准PaddleOCR格式
        if result and len(result) > 0 and isinstance(result[0], list):
            logger.info("检测到旧版本PaddleOCR格式")
            for line in result[0]:
                if not line or len(line) < 2:
                    continue
                
                box, text_info = line[0], line[1]
                
                if not text_info or len(text_info) < 2:
                    continue
                
                text, confidence = text_info[0], text_info[1]
                
                # 过滤低置信度结果
                if confidence >= threshold:
                    formatted_results.append({
                        "box": [[int(x), int(y)] for x, y in box],
                        "text": text,
                        "score": float(confidence)
                    })
        
        return formatted_results
    
    def extract_certificate_info(self, image_path: str, ocr_results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """从证书图片中提取结构化信息
        
        Args:
            image_path: 证书图片路径
            ocr_results: 已有OCR结果（可选，避免重复识别）
        
        Returns:
            证书信息字典
        """
        try:
            if ocr_results is None:
                ocr_results = self.recognize_text(image_path)
            
            all_texts = [r["text"] for r in ocr_results]
            text_content = " ".join(all_texts)
            avg_confidence = sum(r["score"] for r in ocr_results) / len(ocr_results) if ocr_results else 0
            
            # 增强的信息提取模式
            cert_info = {
                "success": True,
                "raw_text": text_content,
                "confidence": round(avg_confidence, 3),
                "name": self._extract_field(text_content, [
                    r'姓名[：:：]\s*([^\s\n，,。.]+)',
                    r'学生[：:：]\s*([^\s\n，,。.]+)',
                    r'获奖者[：:：]\s*([^\s\n，,。.]+)'
                ]),
                "student_id": self._extract_field(text_content, [
                    r'学号[：:：]\s*([0-9]+)',
                    r'学生证号[：:：]\s*([0-9]+)',
                    r'编号[：:：]\s*([0-9]+)'
                ]),
                "title": self._extract_field(text_content, [
                    r'(.*[奖证书])',
                    r'获得\s*([^\s\n，,。.]+[奖证书])',
                    r'荣获\s*([^\s\n，,。.]+[奖证书])'
                ]),
                "level": self._extract_field(text_content, [
                    r'(国家级|省级|市级|校级|院级)',
                    r'(一等奖|二等奖|三等奖|特等奖|优秀奖|优胜奖)'
                ]),
                "issuer": self._extract_field(text_content, [
                    r'(.*大学|.*学院|.*委员会|.*协会)',
                    r'主办[：:：]\s*([^\s\n，,。.]+)',
                    r'颁发单位[：:：]\s*([^\s\n，,。.]+)'
                ]),
                "issue_date": self._extract_field(text_content, [
                    r'(\d{4}年\d{1,2}月\d{1,2}日)',
                    r'(\d{4}-\d{1,2}-\d{1,2})',
                    r'(\d{4}\.\d{1,2}\.\d{1,2})',
                    r'(\d{4}/\d{1,2}/\d{1,2})'
                ]),
            }
            
            # 向后兼容
            cert_info["award_name"] = cert_info["title"]
            cert_info["award_level"] = cert_info["level"]
            cert_info["award_date"] = cert_info["issue_date"]
            
            logger.info(f"证书信息: name={cert_info['name']}, student_id={cert_info['student_id']}, "
                       f"award={cert_info['award_name']}, level={cert_info['award_level']}, "
                       f"conf={cert_info['confidence']:.3f}")
            return cert_info
            
        except Exception as e:
            logger.error(f"证书信息提取失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "raw_text": "",
                "confidence": 0.0
            }
    
    def _extract_field(self, text: str, patterns: List[str]) -> str:
        """使用正则表达式从文本中提取字段
        
        Args:
            text: 要搜索的文本
            patterns: 正则表达式模式列表
            
        Returns:
            提取到的字段值，如果未找到则返回空字符串
        """
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result = match.group(1).strip()
                    if result:
                        return result
            except Exception as e:
                logger.warning(f"正则表达式匹配失败: {pattern}, 错误: {e}")
                continue
        return ""


# 全局单例
_ocr_service_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """获取OCR服务实例（单例模式）"""
    global _ocr_service_instance
    
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService(
            use_gpu=settings.OCR_USE_GPU,
            lang=settings.OCR_LANG
        )
    
    return _ocr_service_instance
