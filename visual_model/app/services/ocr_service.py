#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR服务封装 - 基于PaddleOCR
============================

提供图像OCR识别和证书信息提取功能。
集成模型池和资源监控优化。

示例:
    >>> from app.services.ocr_service import get_ocr_service
    >>> ocr = get_ocr_service()
    >>> results = ocr.recognize_text("image.png")
"""

from __future__ import annotations

import gc
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from PIL import Image

from app.core.logger import logger
from app.core.resource_monitor import get_resource_monitor
from app.services.ocr_model_pool import OCRModelPool, get_ocr_model_pool
from config import settings

if 'DISABLE_MODEL_SOURCE_CHECK' not in os.environ:
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'


class OCRService:
    """PaddleOCR服务封装

    负责图像文字识别和证书信息提取。
    集成模型池管理和资源监控。

    Attributes:
        use_gpu: 是否使用GPU加速
        lang: 识别语言

    Example:
        >>> service = OCRService(use_gpu=False, lang="ch")
        >>> results = service.recognize_text("certificate.jpg")
        >>> info = service.extract_certificate_info("certificate.jpg", results)
    """

    _instance: Optional[OCRService] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, use_gpu: bool = False, lang: str = "ch") -> None:
        """初始化OCR服务

        Args:
            use_gpu: 是否使用GPU加速，默认为False
            lang: 识别语言，默认为中文("ch")
        """
        self.use_gpu: bool = use_gpu
        self.lang: str = lang
        self._initialized: bool = False
        self._model_pool: Optional[OCRModelPool] = None
        self._resource_monitor = get_resource_monitor()

        self._stats: Dict[str, Union[int, float]] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time_ms": 0
        }
        self._stats_lock: threading.Lock = threading.Lock()

        logger.info("OCR服务已创建，模型池将在首次使用时初始化")

    def __del__(self) -> None:
        """析构函数，确保资源释放"""
        pass
    
    def _initialize_model_pool(self) -> None:
        """初始化模型池

        如果已经初始化则跳过，否则创建并配置模型池。
        """
        if self._initialized and self._model_pool is not None:
            return

        logger.info("正在初始化OCR模型池...")

        self._model_pool = get_ocr_model_pool()
        self._model_pool.configure(
            use_gpu=self.use_gpu,
            lang=self.lang,
            max_instances=getattr(settings, 'OCR_MODEL_POOL_SIZE', 1)
        )

        self._initialized = True
        logger.info("OCR模型池初始化完成")

    def warm_up(self) -> None:
        """预热OCR引擎

        提前加载模型以减少首次请求的延迟。
        同时记录预热后的资源状态。
        """
        try:
            self._initialize_model_pool()

            if self._model_pool.preload():
                logger.info("PaddleOCR模型预热完成")
            else:
                logger.warning("PaddleOCR模型预热失败")

            snapshot = self._resource_monitor.take_snapshot()
            logger.info(
                f"预热后资源状态: 内存={snapshot.memory_rss_mb:.1f}MB, "
                f"线程={snapshot.thread_count}"
            )

        except Exception:
            logger.warning("PaddleOCR预热失败，将在首次请求时重试", exc_info=True)
    
    def recognize_text(
        self,
        image_input: Union[str, Path, np.ndarray],
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """识别图像中的文本

        Args:
            image_input: 图像路径或numpy数组
            threshold: 最小置信度阈值，None则使用配置值

        Returns:
            识别结果列表，每个元素包含:
            - box: 文本框坐标列表
            - text: 识别的文本
            - score: 置信度分数

        Raises:
            FileNotFoundError: 图像文件不存在
            ValueError: 图像读取失败
        """
        start_time = time.time()

        with self._stats_lock:
            self._stats["total_requests"] += 1

        img_array = None
        model = None
        
        try:
            self._initialize_model_pool()

            img_array = self._load_image(image_input)
            logger.debug(f"图像加载完成，尺寸: {img_array.shape}")

            model = self._model_pool.acquire_model(timeout=30.0)
            if model is None:
                logger.error("无法获取OCR模型实例")
                with self._stats_lock:
                    self._stats["failed_requests"] += 1
                return []

            try:
                logger.debug("开始OCR识别...")
                result = model.ocr(img_array)
                raw_count = len(result[0]) if result and result[0] else 0
                logger.debug(f"OCR识别完成，检测到 {raw_count} 个文本框")
            finally:
                self._model_pool.release_model(model)
                model = None

            if not result or not result[0]:
                logger.warning("未检测到任何文本框")
                return []

            all_scores: List[float] = []
            for line in result[0]:
                if line and len(line) >= 2 and line[1] and len(line[1]) >= 2:
                    score = float(line[1][1])
                    all_scores.append(score)

            if all_scores:
                logger.debug(
                    f"置信度分布: min={min(all_scores):.3f}, "
                    f"max={max(all_scores):.3f}, "
                    f"avg={sum(all_scores) / len(all_scores):.3f}"
                )

            effective_threshold = (
                threshold if threshold is not None else settings.OCR_THRESHOLD
            )
            min_threshold = 0.01

            all_results = self._format_results(result, min_threshold)
            logger.debug(
                f"原始识别到 {len(all_results)} 条文本（阈值={min_threshold}）"
            )

            filtered_results = [
                r for r in all_results if r['score'] >= effective_threshold
            ]
            logger.debug(
                f"应用阈值 {effective_threshold} 后保留 {len(filtered_results)} 条"
            )

            if len(filtered_results) == 0 and len(all_results) > 0:
                fallback_threshold = (
                    min(0.15, max(all_scores) * 0.8)
                    if all_scores else 0.15
                )
                logger.warning(
                    f"阈值 {effective_threshold} 过高，"
                    f"自动降低至 {fallback_threshold:.3f}"
                )
                filtered_results = [
                    r for r in all_results if r['score'] >= fallback_threshold
                ]
                logger.debug(f"降低阈值后保留 {len(filtered_results)} 条")

            elapsed_ms = (time.time() - start_time) * 1000
            self._resource_monitor.record_ocr_operation(elapsed_ms)

            with self._stats_lock:
                self._stats["successful_requests"] += 1
                self._stats["total_time_ms"] += elapsed_ms

            logger.debug(f"OCR识别完成，耗时: {elapsed_ms:.2f}ms")

            return filtered_results

        except Exception as e:
            logger.error(f"OCR识别失败: {e}", exc_info=True)
            with self._stats_lock:
                self._stats["failed_requests"] += 1
            return []
        finally:
            if img_array is not None:
                del img_array
            if model is not None:
                self._model_pool.release_model(model)
            gc.collect()
    
    def _load_image(self, image_input: Union[str, Path, np.ndarray]) -> np.ndarray:
        """加载图像为numpy数组

        Args:
            image_input: 图像路径或numpy数组

        Returns:
            RGB格式的numpy数组

        Raises:
            FileNotFoundError: 图像文件不存在
            ValueError: 图像读取失败
        """
        if isinstance(image_input, np.ndarray):
            return image_input

        image_path = Path(image_input)
        if not image_path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        try:
            with Image.open(image_path) as img:
                width, height = img.size
                max_dimension = getattr(settings, 'OCR_MAX_IMAGE_SIZE', 1600)

                det_limit = getattr(settings, 'OCR_DET_LIMIT_SIDE_LEN', 960)
                max_dimension = min(max_dimension, det_limit)

                if width > max_dimension or height > max_dimension:
                    ratio = min(max_dimension / width, max_dimension / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    try:
                        resample_filter = Image.LANCZOS
                    except AttributeError:
                        resample_filter = (
                            Image.Resampling.LANCZOS
                            if hasattr(Image, 'Resampling') else 1
                        )
                    img = img.resize((new_width, new_height), resample_filter)
                    logger.debug(
                        f"图像已缩放: {width}x{height} -> {new_width}x{new_height}"
                    )

                result = np.array(img.convert('RGB'))
                
            return result
        except Exception as e:
            logger.error(f"读取图像失败: {e}")
            raise ValueError(f"读取图像失败: {e}")
    
    def _format_results(
        self,
        result: Any,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """格式化OCR识别结果

        支持新旧两种PaddleOCR输出格式。

        Args:
            result: OCR原始识别结果
            threshold: 置信度阈值

        Returns:
            格式化后的结果列表，每个元素包含 box, text, score
        """
        formatted_results: List[Dict[str, Any]] = []

        if not result:
            return formatted_results

        if (
            hasattr(result, '__len__')
            and len(result) > 0
            and hasattr(result[0], 'get')
        ):
            ocr_result = result[0]

            rec_texts = ocr_result.get('rec_texts', [])
            rec_scores = ocr_result.get('rec_scores', [])
            boxes = ocr_result.get('dt_polys', [])

            logger.debug(
                f"新版本OCRResult格式: 文本数={len(rec_texts)}, "
                f"分数数={len(rec_scores)}, 框数={len(boxes)}"
            )

            for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                if score >= threshold:
                    box = (
                        boxes[i].tolist()
                        if i < len(boxes) and hasattr(boxes[i], 'tolist')
                        else []
                    )
                    formatted_results.append({
                        "box": box,
                        "text": text,
                        "score": float(score)
                    })
            return formatted_results

        if result and len(result) > 0 and isinstance(result[0], list):
            logger.debug("检测到旧版本PaddleOCR格式")
            for line in result[0]:
                if not line or len(line) < 2:
                    continue

                box, text_info = line[0], line[1]

                if not text_info or len(text_info) < 2:
                    continue

                text, confidence = text_info[0], text_info[1]

                if confidence >= threshold:
                    formatted_results.append({
                        "box": [[int(x), int(y)] for x, y in box],
                        "text": text,
                        "score": float(confidence)
                    })

        return formatted_results
    
    def extract_certificate_info(
        self,
        image_path: str,
        ocr_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """从证书图片中提取结构化信息

        Args:
            image_path: 证书图片路径
            ocr_results: 已有OCR结果，可选，避免重复识别

        Returns:
            证书信息字典，包含:
            - success: 是否成功
            - raw_text: 原始文本
            - confidence: 平均置信度
            - name: 姓名
            - student_id: 学号
            - title: 证书标题
            - level: 获奖级别
            - issuer: 颁发单位
            - issue_date: 颁发日期
            - award_name: 奖项名称（同title）
            - award_level: 奖项级别（同level）
            - award_date: 获奖日期（同issue_date）
        """
        try:
            if ocr_results is None:
                ocr_results = self.recognize_text(image_path)

            all_texts = [r["text"] for r in ocr_results]
            text_content = " ".join(all_texts)
            avg_confidence = (
                sum(r["score"] for r in ocr_results) / len(ocr_results)
                if ocr_results else 0
            )

            cert_info: Dict[str, Any] = {
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

            cert_info["award_name"] = cert_info["title"]
            cert_info["award_level"] = cert_info["level"]
            cert_info["award_date"] = cert_info["issue_date"]

            logger.debug(
                f"证书信息: name={cert_info['name']}, "
                f"student_id={cert_info['student_id']}, "
                f"award={cert_info['award_name']}, "
                f"level={cert_info['award_level']}, "
                f"conf={cert_info['confidence']:.3f}"
            )
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
            patterns: 正则表达式模式列表，按优先级排序

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

    def get_stats(self) -> Dict[str, Any]:
        """获取OCR服务统计信息

        Returns:
            统计信息字典，包含:
            - total_requests: 总请求数
            - successful_requests: 成功请求数
            - failed_requests: 失败请求数
            - total_time_ms: 总耗时（毫秒）
            - avg_time_ms: 平均耗时（毫秒）
        """
        with self._stats_lock:
            avg_time = (
                self._stats["total_time_ms"] / self._stats["successful_requests"]
                if self._stats["successful_requests"] > 0 else 0
            )
            return {
                **self._stats,
                "avg_time_ms": round(avg_time, 2)
            }

    def get_model_pool_status(self) -> Dict[str, Any]:
        """获取模型池状态

        Returns:
            模型池状态字典，包含:
            - status: 状态（not_initialized/initialized）
            - 其他模型池特定信息
        """
        if self._model_pool is None:
            return {"status": "not_initialized"}
        return self._model_pool.get_status()


_ocr_service_instance: Optional[OCRService] = None
_lock: threading.Lock = threading.Lock()


def get_ocr_service() -> OCRService:
    """获取OCR服务实例（线程安全单例模式）

    Returns:
        OCRService实例
    """
    global _ocr_service_instance

    if _ocr_service_instance is None:
        with _lock:
            if _ocr_service_instance is None:
                _ocr_service_instance = OCRService(
                    use_gpu=settings.OCR_USE_GPU,
                    lang=settings.OCR_LANG
                )

    return _ocr_service_instance
