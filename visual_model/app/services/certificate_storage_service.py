#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书存储服务
============

支持多张证书图片上传、存储、OCR处理。

示例:
    >>> from app.services.certificate_storage_service import get_certificate_storage_service
    >>> service = get_certificate_storage_service()
    >>> result = await service.upload_certificate_images(
    ...     student_id="2023001",
    ...     files=[("cert.jpg", file_bytes)]
    ... )
"""

from __future__ import annotations

import asyncio
import gc
import hashlib
import io
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PIL import Image

from app.core.logger import get_logger
from app.models.tortoise_models import Certificate, CertificateBatch, CertificateImage, Student

logger = get_logger(__name__)


class CertificateStorageService:
    """证书存储服务

    负责证书图片的上传、存储和管理。

    Attributes:
        UPLOAD_DIR: 上传目录路径
        THUMBNAIL_DIR: 缩略图目录路径
        ALLOWED_EXTENSIONS: 允许的文件扩展名集合
        MAX_FILE_SIZE: 最大文件大小（字节）
    """

    UPLOAD_DIR: Path = Path("uploads/certificates")
    THUMBNAIL_DIR: Path = Path("uploads/certificates/thumbnails")
    ALLOWED_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf'}
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    def __init__(self) -> None:
        """初始化证书存储服务"""
        self.upload_dir: Path = self.UPLOAD_DIR
        self.thumbnail_dir: Path = self.THUMBNAIL_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"证书存储服务初始化完成, 上传目录: {self.upload_dir}")
    
    def _log_data_trace(self, step: str, data: Any) -> None:
        """数据追踪日志

        Args:
            step: 当前步骤名称
            data: 要记录的数据
        """
        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, ensure_ascii=False, indent=2)
                if len(data_str) > 1000:
                    data_str = data_str[:1000] + "..."
            except Exception:
                data_str = str(data)[:1000]
        else:
            data_str = str(data)[:1000]

        logger.info(f"[证书存储-{step}]\n{data_str}")

    def _calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件MD5哈希值

        Args:
            file_content: 文件二进制内容

        Returns:
            MD5哈希字符串
        """
        return hashlib.md5(file_content).hexdigest()

    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名

        Args:
            filename: 文件名

        Returns:
            小写的文件扩展名（包含点号）
        """
        return Path(filename).suffix.lower()

    def _validate_file(
        self,
        filename: str,
        file_content: bytes
    ) -> Tuple[bool, str]:
        """验证文件

        Args:
            filename: 文件名
            file_content: 文件二进制内容

        Returns:
            元组 (是否验证通过, 错误消息)
        """
        ext = self._get_file_extension(filename)
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"不支持的文件格式: {ext}"

        if len(file_content) > self.MAX_FILE_SIZE:
            return False, (
                f"文件大小超过限制: {len(file_content)} > {self.MAX_FILE_SIZE}"
            )

        return True, "验证通过"
    
    async def upload_certificate_images(
        self,
        student_id: str,
        files: List[Tuple[str, bytes]],
        certificate_info: Optional[Dict[str, Any]] = None,
        upload_ip: Optional[str] = None,
        upload_device: Optional[str] = None
    ) -> Dict[str, Any]:
        """上传证书图片（支持多张）

        Args:
            student_id: 学号
            files: 文件列表 [(filename, file_content), ...]
            certificate_info: 证书基本信息
            upload_ip: 上传IP地址
            upload_device: 上传设备信息

        Returns:
            上传结果字典，包含:
            - success: 是否成功
            - certificate_id: 证书ID
            - batch_id: 批次ID
            - success_count: 成功上传数量
            - failed_count: 失败数量
            - images: 上传成功的图片列表
        """
        self._log_data_trace("开始上传证书", {
            "student_id": student_id,
            "file_count": len(files)
        })

        batch_id = str(uuid.uuid4())

        batch = await CertificateBatch.create(
            batch_id=batch_id,
            student_id=student_id,
            total_count=len(files),
            status="processing",
            upload_ip=upload_ip,
            upload_device=upload_device,
            started_at=datetime.now()
        )

        try:
            student = await Student.get_or_none(id=student_id)
            if not student:
                await self._update_batch_failed(batch, "学生不存在")
                return {"success": False, "error": "学生不存在"}

            first_uploaded_file = files[0] if files else None
            first_filename = files[0][0] if files else "unknown"

            certificate = await Certificate.create(
                student_id=student_id,
                filename=first_filename,
                title=certificate_info.get("title") if certificate_info else None,
                certificate_type=certificate_info.get("certificate_type") if certificate_info else None,
                level=certificate_info.get("level") if certificate_info else None,
                issuer=certificate_info.get("issuer") if certificate_info else None,
                issue_date=certificate_info.get("issue_date") if certificate_info else None,
                category=certificate_info.get("category", "C") if certificate_info else "C",
                sub_category=certificate_info.get("sub_category") if certificate_info else None,
                upload_batch_id=batch_id,
                source="upload"
            )

            uploaded_images: List[Dict[str, Any]] = []
            success_count: int = 0
            failed_count: int = 0

            for idx, (filename, file_content) in enumerate(files):
                try:
                    is_valid, msg = self._validate_file(filename, file_content)
                    if not is_valid:
                        failed_count += 1
                        logger.warning(f"文件验证失败: {filename}, {msg}")
                        continue

                    image = await self._save_certificate_image(
                        certificate_id=certificate.id,
                        student_id=student_id,
                        filename=filename,
                        file_content=file_content,
                        image_order=idx,
                        is_primary=(idx == 0),
                        upload_ip=upload_ip,
                        upload_device=upload_device
                    )

                    uploaded_images.append({
                        "image_id": image.id,
                        "filename": filename,
                        "file_path": image.file_path
                    })
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error(f"保存图片失败: {filename}, {e}")

            certificate.image_count = success_count
            if uploaded_images:
                certificate.primary_image_id = uploaded_images[0]["image_id"]
            await certificate.save()

            batch.status = "completed"
            batch.success_count = success_count
            batch.failed_count = failed_count
            batch.completed_at = datetime.now()
            await batch.save()

            self._log_data_trace("上传完成", {
                "certificate_id": certificate.id,
                "success_count": success_count,
                "failed_count": failed_count
            })

            # 异步触发OCR处理
            try:
                from app.services.certificate_ocr_processing_service import get_certificate_ocr_processing_service
                ocr_processing_service = get_certificate_ocr_processing_service()
                asyncio.create_task(ocr_processing_service.process_certificate(certificate))
                logger.info(f"已触发OCR处理: certificate_id={certificate.id}")
            except Exception as e:
                logger.warning(f"触发OCR处理失败: {e}", exc_info=True)

            return {
                "success": True,
                "certificate_id": certificate.id,
                "batch_id": batch_id,
                "success_count": success_count,
                "failed_count": failed_count,
                "images": uploaded_images
            }

        except Exception as e:
            logger.error(f"上传证书失败: {e}", exc_info=True)
            await self._update_batch_failed(batch, str(e))
            return {"success": False, "error": str(e)}
    
    async def _save_certificate_image(
        self,
        certificate_id: int,
        student_id: str,
        filename: str,
        file_content: bytes,
        image_order: int,
        is_primary: bool,
        upload_ip: Optional[str] = None,
        upload_device: Optional[str] = None
    ) -> CertificateImage:
        """保存证书图片

        Args:
            certificate_id: 证书ID
            student_id: 学号
            filename: 文件名
            file_content: 文件二进制内容
            image_order: 图片顺序
            is_primary: 是否为主图
            upload_ip: 上传IP地址
            upload_device: 上传设备信息

        Returns:
            创建的CertificateImage对象
        """
        file_hash = self._calculate_file_hash(file_content)
        ext = self._get_file_extension(filename)

        file_id = str(uuid.uuid4())
        stored_filename = f"{file_id}{ext}"

        student_dir = self.upload_dir / student_id
        student_dir.mkdir(parents=True, exist_ok=True)

        file_path = student_dir / stored_filename

        with open(file_path, 'wb') as f:
            f.write(file_content)

        image_width, image_height = self._get_image_dimensions(file_content, ext)

        image = await CertificateImage.create(
            certificate_id=certificate_id,
            student_id=student_id,
            file_id=file_id,
            filename=filename,
            file_path=str(file_path),
            file_size=len(file_content),
            file_hash=file_hash,
            image_width=image_width,
            image_height=image_height,
            image_format=ext.lstrip('.'),
            is_primary=is_primary,
            image_order=image_order,
            upload_ip=upload_ip,
            upload_device=upload_device
        )

        self._log_data_trace(f"保存图片成功", {
            "image_id": image.id,
            "filename": filename,
            "file_path": str(file_path)
        })

        return image

    def _get_image_dimensions(
        self,
        file_content: bytes,
        ext: str
    ) -> Tuple[Optional[int], Optional[int]]:
        """获取图片尺寸

        Args:
            file_content: 文件二进制内容
            ext: 文件扩展名

        Returns:
            元组 (宽度, 高度)，PDF文件返回 (None, None)
        """
        img = None
        try:
            if ext.lower() == '.pdf':
                return None, None

            img = Image.open(io.BytesIO(file_content))
            size = img.size
            return size
        except Exception as e:
            logger.warning(f"获取图片尺寸失败: {e}")
            return None, None
        finally:
            if img is not None:
                try:
                    img.close()
                except Exception:
                    pass
            del img
            gc.collect()

    async def _update_batch_failed(
        self,
        batch: CertificateBatch,
        error_message: str
    ) -> None:
        """更新批次状态为失败

        Args:
            batch: 批次对象
            error_message: 错误消息
        """
        batch.status = "failed"
        batch.error_message = error_message
        batch.completed_at = datetime.now()
        await batch.save()
    
    async def get_student_certificates(
        self,
        student_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取学生证书列表

        Args:
            student_id: 学号
            status: 证书状态筛选
            category: 证书类别筛选

        Returns:
            证书列表，每个证书包含基本信息和图片列表
        """
        query = Certificate.filter(student_id=student_id, is_valid=True)

        if status:
            query = query.filter(status=status)
        if category:
            query = query.filter(category=category)

        certificates = await query.order_by('-created_at').all()
        
        if not certificates:
            return []
        
        cert_ids = [cert.id for cert in certificates]
        all_images = await CertificateImage.filter(
            certificate_id__in=cert_ids
        ).order_by('certificate_id', 'image_order').all()
        
        images_by_cert: Dict[int, List[CertificateImage]] = {}
        for img in all_images:
            if img.certificate_id not in images_by_cert:
                images_by_cert[img.certificate_id] = []
            images_by_cert[img.certificate_id].append(img)

        result: List[Dict[str, Any]] = []
        for cert in certificates:
            cert_images = images_by_cert.get(cert.id, [])
            result.append({
                "id": cert.id,
                "student_id": cert.student_id,
                "title": cert.title,
                "certificate_type": cert.certificate_type,
                "level": cert.level,
                "issuer": cert.issuer,
                "issue_date": cert.issue_date,
                "category": cert.category,
                "sub_category": cert.sub_category,
                "score": cert.score,
                "status": cert.status,
                "image_count": cert.image_count,
                "images": [{
                    "id": img.id,
                    "filename": img.filename,
                    "file_path": img.file_path,
                    "is_primary": img.is_primary,
                    "image_order": img.image_order
                } for img in cert_images],
                "created_at": cert.created_at.isoformat() if cert.created_at else None
            })

        return result

    async def get_certificate_detail(self, certificate_id: int) -> Dict[str, Any]:
        """获取证书详情

        Args:
            certificate_id: 证书ID

        Returns:
            证书详情字典，包含完整的证书信息和所有图片信息
        """
        certificate = await Certificate.get_or_none(id=certificate_id)
        if not certificate:
            return {"success": False, "error": "证书不存在"}

        images = await CertificateImage.filter(
            certificate_id=certificate_id
        ).order_by('image_order').all()

        return {
            "success": True,
            "certificate": {
                "id": certificate.id,
                "student_id": certificate.student_id,
                "certificate_no": certificate.certificate_no,
                "title": certificate.title,
                "certificate_type": certificate.certificate_type,
                "level": certificate.level,
                "issuer": certificate.issuer,
                "issue_date": certificate.issue_date,
                "expiry_date": certificate.expiry_date,
                "category": certificate.category,
                "sub_category": certificate.sub_category,
                "score": certificate.score,
                "classification_reason": certificate.classification_reason,
                "status": certificate.status,
                "reviewed_by": certificate.reviewed_by,
                "reviewed_at": certificate.reviewed_at.isoformat() if certificate.reviewed_at else None,
                "review_comment": certificate.review_comment,
                "raw_text": certificate.raw_text,
                "certificate_info": certificate.certificate_info,
                "image_count": certificate.image_count,
                "images": [{
                    "id": img.id,
                    "filename": img.filename,
                    "file_path": img.file_path,
                    "file_size": img.file_size,
                    "image_width": img.image_width,
                    "image_height": img.image_height,
                    "image_format": img.image_format,
                    "is_primary": img.is_primary,
                    "image_order": img.image_order,
                    "ocr_processed": img.ocr_processed,
                    "ocr_text": img.ocr_text
                } for img in images],
                "created_at": certificate.created_at.isoformat() if certificate.created_at else None,
                "updated_at": certificate.updated_at.isoformat() if certificate.updated_at else None
            }
        }

    async def delete_certificate(
        self,
        certificate_id: int,
        deleted_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """删除证书（软删除）

        Args:
            certificate_id: 证书ID
            deleted_by: 删除人标识

        Returns:
            操作结果字典
        """
        certificate = await Certificate.get_or_none(id=certificate_id).prefetch_related('student')
        if not certificate:
            return {"success": False, "error": "证书不存在"}

        # 保存学生ID用于缓存失效
        student_id = certificate.student_id if hasattr(certificate, 'student_id') else None
        
        # 执行软删除
        certificate.is_valid = False
        certificate.invalid_reason = f"用户删除 - {deleted_by}"
        certificate.status = "deleted"
        await certificate.save()

        # 删除关联的图片文件（可选）
        try:
            images = await CertificateImage.filter(certificate_id=certificate_id).all()
            for image in images:
                if image.file_path and os.path.exists(image.file_path):
                    os.remove(image.file_path)
                    logger.info(f"已删除文件: {image.file_path}")
        except Exception as e:
            logger.warning(f"删除关联文件失败: {e}")

        # 使缓存失效
        await self._invalidate_cache(student_id)

        self._log_data_trace("删除证书", {
            "certificate_id": certificate_id,
            "deleted_by": deleted_by,
            "student_id": student_id
        })

        return {
            "success": True, 
            "message": "证书已删除",
            "certificate_id": certificate_id,
            "student_id": student_id
        }

    async def _invalidate_cache(self, student_id: Optional[str] = None):
        """使缓存失效
        
        Args:
            student_id: 学生ID
        """
        try:
            # 使学生上传历史缓存失效
            if student_id:
                from app.core.cache_service import get_cache_service
                cache_service = get_cache_service()
                cache_service.invalidate_student(student_id)
                logger.info(f"已使学生 {student_id} 的缓存失效")
        except Exception as e:
            logger.warning(f"缓存失效失败: {e}")

    async def update_certificate_info(
        self,
        certificate_id: int,
        info: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新证书信息

        Args:
            certificate_id: 证书ID
            info: 要更新的字段字典
            updated_by: 更新人标识

        Returns:
            操作结果字典
        """
        certificate = await Certificate.get_or_none(id=certificate_id)
        if not certificate:
            return {"success": False, "error": "证书不存在"}

        updatable_fields = [
            'title', 'certificate_type', 'level', 'issuer', 'issue_date',
            'expiry_date', 'category', 'sub_category', 'score',
            'classification_reason', 'certificate_no'
        ]

        for field in updatable_fields:
            if field in info:
                setattr(certificate, field, info[field])

        await certificate.save()

        self._log_data_trace("更新证书信息", {
            "certificate_id": certificate_id,
            "updated_by": updated_by
        })

        return {"success": True, "certificate_id": certificate_id}

    async def get_certificate_statistics(self, student_id: str) -> Dict[str, Any]:
        """获取学生证书统计

        Args:
            student_id: 学号

        Returns:
            统计信息字典，包含:
            - student_id: 学号
            - total_certificates: 总证书数
            - approved_count: 已通过数量
            - pending_count: 待审核数量
            - rejected_count: 已拒绝数量
            - category_statistics: 各类别统计
            - total_score: 总分数
        """
        certificates = await Certificate.filter(
            student_id=student_id, is_valid=True
        ).only('id', 'category', 'sub_category', 'status', 'score')
        
        total = len(certificates)
        approved_count = 0
        pending_count = 0
        rejected_count = 0
        category_stats: Dict[str, int] = {'A': 0, 'C1': 0, 'C2': 0, 'C3': 0, 'C4': 0}
        total_score = 0.0
        
        for cert in certificates:
            if cert.status == "approved":
                approved_count += 1
                total_score += cert.score or 0
                
                if cert.category == 'A':
                    category_stats['A'] += 1
                elif cert.sub_category in category_stats:
                    category_stats[cert.sub_category] += 1
            elif cert.status == "pending":
                pending_count += 1
            elif cert.status == "rejected":
                rejected_count += 1

        return {
            "student_id": student_id,
            "total_certificates": total,
            "approved_count": approved_count,
            "pending_count": pending_count,
            "rejected_count": rejected_count,
            "category_statistics": category_stats,
            "total_score": total_score
        }


certificate_storage_service = CertificateStorageService()


def get_certificate_storage_service() -> CertificateStorageService:
    """获取证书存储服务实例"""
    return certificate_storage_service
