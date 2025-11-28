#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理服务

提供完整的图像预处理、格式转换、压缩、OCR优化等功能。
整合了PIL和OpenCV两种图像处理库的优势。
"""

from typing import Union, Tuple, Optional
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from app.core.logger import logger


class ImageService:
    """图像处理服务
    
    提供基于PIL和OpenCV的完整图像处理功能，包括：
    - 基础操作：加载、保存、调整大小、裁剪
    - 图像增强：对比度、清晰度、去噪
    - 格式转换：PIL/CV2/numpy互转
    - OCR优化：倾斜校正、对比度增强、去噪等
    """
    
    def __init__(self):
        """初始化图像处理服务"""
        logger.info("图像处理服务已初始化")
    
    # ============================================================================
    # 基础操作：加载、保存、转换
    # ============================================================================
    
    def load_image(self, image_input: Union[str, Path, np.ndarray, bytes, io.BytesIO]) -> Image.Image:
        """加载图像
        
        Args:
            image_input: 图像路径、numpy数组、字节数据或BytesIO对象
            
        Returns:
            PIL Image对象
        """
        try:
            if isinstance(image_input, (str, Path)):
                image_path = Path(image_input)
                if not image_path.exists():
                    raise FileNotFoundError(f"图像文件不存在: {image_path}")
                return Image.open(image_path)
            elif isinstance(image_input, np.ndarray):
                return Image.fromarray(image_input)
            elif isinstance(image_input, bytes):
                return Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, io.BytesIO):
                return Image.open(image_input)
            else:
                raise ValueError(f"不支持的图像输入类型: {type(image_input)}")
        except Exception as e:
            logger.error(f"加载图像失败: {e}")
            raise
    
    def save_image(self, image: Image.Image, output_path: Union[str, Path], quality: int = 95) -> None:
        """保存图像
        
        Args:
            image: PIL Image对象
            output_path: 输出路径
            quality: 图像质量 (1-100)
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 根据文件扩展名确定格式
            format_type = None
            if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                format_type = 'JPEG'
            elif output_path.suffix.lower() == '.png':
                format_type = 'PNG'
            
            image.save(output_path, format=format_type, quality=quality)
            logger.info(f"图像已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存图像失败: {e}")
            raise
    
    def pil_to_cv2(self, image: Image.Image) -> np.ndarray:
        """将PIL图像转换为OpenCV格式
        
        Args:
            image: PIL Image对象
            
        Returns:
            OpenCV格式的numpy数组
        """
        img_cv = np.array(image)
        if len(img_cv.shape) == 3 and img_cv.shape[2] == 3:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        return img_cv
    
    def cv2_to_pil(self, img_cv: np.ndarray) -> Image.Image:
        """将OpenCV图像转换为PIL格式
        
        Args:
            img_cv: OpenCV格式的numpy数组
            
        Returns:
            PIL Image对象
        """
        if len(img_cv.shape) == 3 and img_cv.shape[2] == 3:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        return Image.fromarray(img_cv)
    
    def get_image_info(self, image: Image.Image) -> dict:
        """获取图像信息
        
        Args:
            image: PIL Image对象
            
        Returns:
            图像信息字典
        """
        try:
            info = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format,
                "size_bytes": len(image.tobytes()) if hasattr(image, 'tobytes') else None
            }
            return info
        except Exception as e:
            logger.error(f"获取图像信息失败: {e}")
            raise
    
    # ============================================================================
    # 基础图像操作：调整大小、裁剪、格式转换
    # ============================================================================
    
    def resize_image(self, image: Union[Image.Image, np.ndarray], 
                    size: Optional[Tuple[int, int]] = None, 
                    max_size: Optional[int] = None,
                    keep_aspect: bool = True) -> Union[Image.Image, np.ndarray]:
        """调整图像大小（支持PIL和CV2格式）
        
        Args:
            image: PIL Image对象或numpy数组
            size: 目标尺寸 (width, height)
            max_size: 最长边的最大尺寸（保持宽高比）
            keep_aspect: 是否保持宽高比
            
        Returns:
            调整大小后的图像（保持输入格式）
        """
        try:
            is_cv2 = isinstance(image, np.ndarray)
            
            if is_cv2:
                h, w = image.shape[:2]
                
                if max_size and max(h, w) > max_size:
                    scale = max_size / max(h, w)
                    new_w, new_h = int(w * scale), int(h * scale)
                    resized = cv2.resize(image, (new_w, new_h))
                elif size:
                    if keep_aspect:
                        ratio = min(size[0] / w, size[1] / h)
                        new_w, new_h = int(w * ratio), int(h * ratio)
                        resized = cv2.resize(image, (new_w, new_h))
                    else:
                        resized = cv2.resize(image, size)
                else:
                    resized = image
                
                logger.debug(f"图像大小已调整 (CV2): {(w, h)} -> {(resized.shape[1], resized.shape[0])}")
                return resized
            else:
                # PIL格式
                if max_size and max(image.width, image.height) > max_size:
                    ratio = max_size / max(image.width, image.height)
                    new_size = (int(image.width * ratio), int(image.height * ratio))
                    resized = image.resize(new_size, Image.LANCZOS)
                elif size:
                    if keep_aspect:
                        ratio = min(size[0] / image.width, size[1] / image.height)
                        new_size = (int(image.width * ratio), int(image.height * ratio))
                        resized = image.resize(new_size, Image.LANCZOS)
                    else:
                        resized = image.resize(size, Image.LANCZOS)
                else:
                    resized = image
                
                logger.debug(f"图像大小已调整 (PIL): {(image.width, image.height)} -> {(resized.width, resized.height)}")
                return resized
                
        except Exception as e:
            logger.error(f"调整图像大小失败: {e}")
            raise
    
    def crop_image(self, image: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
        """裁剪图像
        
        Args:
            image: PIL Image对象
            box: 裁剪区域 (left, top, right, bottom)
            
        Returns:
            裁剪后的图像
        """
        try:
            cropped_image = image.crop(box)
            logger.debug(f"图像已裁剪: {box}")
            return cropped_image
        except Exception as e:
            logger.error(f"裁剪图像失败: {e}")
            raise
    
    def convert_to_grayscale(self, image: Union[Image.Image, np.ndarray]) -> Union[Image.Image, np.ndarray]:
        """转换为灰度图像（支持PIL和CV2格式）
        
        Args:
            image: PIL Image对象或numpy数组
            
        Returns:
            灰度图像（保持输入格式）
        """
        try:
            if isinstance(image, np.ndarray):
                # CV2格式
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    logger.debug("图像已转换为灰度 (CV2)")
                    return gray
                return image
            else:
                # PIL格式
                grayscale_image = image.convert('L')
                logger.debug("图像已转换为灰度 (PIL)")
                return grayscale_image
        except Exception as e:
            logger.error(f"转换为灰度图像失败: {e}")
            raise
    
    def convert_to_rgb(self, image: Image.Image) -> Image.Image:
        """转换为RGB图像
        
        Args:
            image: PIL Image对象
            
        Returns:
            RGB图像
        """
        try:
            rgb_image = image.convert('RGB')
            logger.debug("图像已转换为RGB")
            return rgb_image
        except Exception as e:
            logger.error(f"转换为RGB图像失败: {e}")
            raise
    
    # ============================================================================
    # 图像增强：对比度、清晰度、去噪
    # ============================================================================
    
    def enhance_contrast_pil(self, image: Image.Image, factor: float = 1.5) -> Image.Image:
        """增强图像对比度（PIL方法）
        
        Args:
            image: PIL Image对象
            factor: 对比度因子，1.0表示原始对比度
            
        Returns:
            增强对比度后的图像
        """
        try:
            enhancer = ImageEnhance.Contrast(image)
            enhanced_image = enhancer.enhance(factor)
            logger.debug(f"图像对比度已增强 (PIL)，因子: {factor}")
            return enhanced_image
        except Exception as e:
            logger.error(f"增强图像对比度失败: {e}")
            raise
    
    def enhance_contrast_cv2(self, img: np.ndarray) -> np.ndarray:
        """增强图像对比度（CV2方法，使用CLAHE自适应直方图均衡化）
        
        Args:
            img: OpenCV格式的numpy数组
            
        Returns:
            增强对比度后的图像
        """
        try:
            # 如果是彩色图像，先转换为灰度
            if len(img.shape) == 3:
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                is_color = True
            else:
                img_gray = img.copy()
                is_color = False
            
            # 应用CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(img_gray)
            
            # 如果原图是彩色，转回彩色
            if is_color:
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            logger.debug("图像对比度已增强 (CV2 CLAHE)")
            return enhanced
        except Exception as e:
            logger.error(f"增强图像对比度失败 (CV2): {e}")
            raise
    
    def enhance_sharpness(self, image: Image.Image, factor: float = 1.5) -> Image.Image:
        """增强图像清晰度
        
        Args:
            image: PIL Image对象
            factor: 清晰度因子，1.0表示原始清晰度
            
        Returns:
            增强清晰度后的图像
        """
        try:
            enhancer = ImageEnhance.Sharpness(image)
            enhanced_image = enhancer.enhance(factor)
            logger.debug(f"图像清晰度已增强，因子: {factor}")
            return enhanced_image
        except Exception as e:
            logger.error(f"增强图像清晰度失败: {e}")
            raise
    
    def denoise_image(self, img: np.ndarray) -> np.ndarray:
        """去除图像噪声
        
        使用双边滤波（彩色图）或中值滤波（灰度图）去噪，保留边缘细节。
        
        Args:
            img: OpenCV格式的numpy数组
            
        Returns:
            去噪后的图像
        """
        try:
            if len(img.shape) == 3:
                # 彩色图像使用双边滤波
                denoised = cv2.bilateralFilter(img, 9, 75, 75)
            else:
                # 灰度图像使用中值滤波
                denoised = cv2.medianBlur(img, 5)
            
            logger.debug("图像已去噪")
            return denoised
        except Exception as e:
            logger.error(f"去噪失败: {e}")
            raise
    
    def apply_gaussian_blur(self, image: Image.Image, radius: float = 1.0) -> Image.Image:
        """应用高斯模糊
        
        Args:
            image: PIL Image对象
            radius: 模糊半径
            
        Returns:
            模糊后的图像
        """
        try:
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=radius))
            logger.debug(f"已应用高斯模糊，半径: {radius}")
            return blurred_image
        except Exception as e:
            logger.error(f"应用高斯模糊失败: {e}")
            raise
    
    # ============================================================================
    # OCR优化：倾斜校正、预处理
    # ============================================================================
    
    def deskew_image(self, img: np.ndarray) -> np.ndarray:
        """倾斜校正
        
        基于最小外接矩形的倾斜校正，适用于文档图像。
        
        Args:
            img: OpenCV格式的numpy数组
            
        Returns:
            校正后的图像
        """
        try:
            # 转换为灰度图
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()
            
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 找到最大的轮廓
            if not contours:
                logger.debug("未检测到轮廓，跳过倾斜校正")
                return img
            
            max_contour = max(contours, key=cv2.contourArea)
            
            # 计算最小外接矩形
            rect = cv2.minAreaRect(max_contour)
            angle = rect[2]
            
            # 调整角度
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # 角度太小则不校正
            if abs(angle) < 0.5:
                logger.debug(f"倾斜角度太小 ({angle:.2f}度)，跳过校正")
                return img
            
            # 获取图像中心点
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            
            # 生成旋转矩阵
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # 执行旋转
            rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            logger.debug(f"图像已校正倾斜，角度: {angle:.2f}度")
            return rotated
            
        except Exception as e:
            logger.error(f"倾斜校正失败: {e}")
            return img
    
    def preprocess_for_ocr(self, image: Union[Image.Image, str, Path], 
                          max_size: int = 1600,
                          enhance_contrast: bool = True,
                          denoise: bool = True,
                          deskew: bool = True) -> np.ndarray:
        """为OCR识别准备图像的完整预处理流水线
        
        Args:
            image: PIL Image对象或图像路径
            max_size: 最大尺寸（最长边）
            enhance_contrast: 是否增强对比度
            denoise: 是否去噪
            deskew: 是否倾斜校正
            
        Returns:
            预处理后的OpenCV格式图像
        """
        try:
            # 加载图像
            if not isinstance(image, Image.Image):
                image = self.load_image(image)
            
            # 转换为OpenCV格式
            img_cv = self.pil_to_cv2(image)
            
            # 调整大小
            img_cv = self.resize_image(img_cv, max_size=max_size)
            
            # 去噪
            if denoise:
                img_cv = self.denoise_image(img_cv)
            
            # 对比度增强
            if enhance_contrast:
                img_cv = self.enhance_contrast_cv2(img_cv)
            
            # 倾斜校正
            if deskew:
                img_cv = self.deskew_image(img_cv)
            
            logger.info("OCR预处理完成")
            return img_cv
            
        except Exception as e:
            logger.error(f"OCR预处理失败: {e}")
            raise
    
    # ============================================================================
    # 图像压缩与优化
    # ============================================================================
    
    def compress_image(self, image: Image.Image, 
                      quality: int = 85, 
                      max_size: Optional[Tuple[int, int]] = None) -> Image.Image:
        """压缩图像
        
        Args:
            image: PIL Image对象
            quality: 压缩质量 (1-100)
            max_size: 最大尺寸 (width, height)，如果超过则调整大小
            
        Returns:
            压缩后的图像
        """
        try:
            # 如果需要，先调整大小
            if max_size and (image.width > max_size[0] or image.height > max_size[1]):
                image = self.resize_image(image, size=max_size, keep_aspect=True)
            
            # 保存为临时字节流以压缩
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality)
            output.seek(0)
            
            # 重新加载压缩后的图像
            compressed_image = Image.open(output)
            logger.debug(f"图像已压缩，质量: {quality}")
            return compressed_image
        except Exception as e:
            logger.error(f"压缩图像失败: {e}")
            raise


# ============================================================================
# 全局服务实例
# ============================================================================

_image_service_instance = None


def get_image_service() -> ImageService:
    """获取图像服务的全局单例实例
    
    Returns:
        ImageService实例
    """
    global _image_service_instance
    if _image_service_instance is None:
        _image_service_instance = ImageService()
    return _image_service_instance
