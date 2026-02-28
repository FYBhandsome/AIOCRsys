#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书存储服务
支持多张证书图片上传、存储、OCR处理
"""
import json
import os
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.core.logger import get_logger
from app.models.tortoise_models import (
    Certificate, CertificateImage, CertificateBatch, Student
)

logger = get_logger(__name__)


class CertificateStorageService:
    """证书存储服务"""
    
    UPLOAD_DIR = Path("uploads/certificates")
    THUMBNAIL_DIR = Path("uploads/certificates/thumbnails")
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        self.upload_dir = self.UPLOAD_DIR
        self.thumbnail_dir = self.THUMBNAIL_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"证书存储服务初始化完成, 上传目录: {self.upload_dir}")
    
    def _log_data_trace(self, step: str, data: Any):
        """数据追踪日志"""
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
        """计算文件MD5哈希值"""
        return hashlib.md5(file_content).hexdigest()
    
    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return Path(filename).suffix.lower()
    
    def _validate_file(self, filename: str, file_content: bytes) -> Tuple[bool, str]:
        """验证文件"""
        ext = self._get_file_extension(filename)
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"不支持的文件格式: {ext}"
        
        if len(file_content) > self.MAX_FILE_SIZE:
            return False, f"文件大小超过限制: {len(file_content)} > {self.MAX_FILE_SIZE}"
        
        return True, "验证通过"
    
    async def upload_certificate_images(
        self,
        student_id: str,
        files: List[Tuple[str, bytes]],
        certificate_info: Dict[str, Any] = None,
        upload_ip: str = None,
        upload_device: str = None
    ) -> Dict[str, Any]:
        """
        上传证书图片（支持多张）
        
        Args:
            student_id: 学号
            files: 文件列表 [(filename, file_content), ...]
            certificate_info: 证书基本信息
            upload_ip: 上传IP
            upload_device: 上传设备
            
        Returns:
            上传结果
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
            
            certificate = await Certificate.create(
                student_id=student_id,
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
            
            uploaded_images = []
            success_count = 0
            failed_count = 0
            
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
        upload_ip: str = None,
        upload_device: str = None
    ) -> CertificateImage:
        """保存证书图片"""
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
    
    def _get_image_dimensions(self, file_content: bytes, ext: str) -> Tuple[Optional[int], Optional[int]]:
        """获取图片尺寸"""
        try:
            from PIL import Image
            import io
            
            if ext.lower() == '.pdf':
                return None, None
            
            img = Image.open(io.BytesIO(file_content))
            return img.size
        except Exception as e:
            logger.warning(f"获取图片尺寸失败: {e}")
            return None, None
    
    async def _update_batch_failed(self, batch: CertificateBatch, error_message: str):
        """更新批次状态为失败"""
        batch.status = "failed"
        batch.error_message = error_message
        batch.completed_at = datetime.now()
        await batch.save()
    
    async def get_student_certificates(
        self,
        student_id: str,
        status: str = None,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """获取学生证书列表"""
        query = Certificate.filter(student_id=student_id, is_valid=True)
        
        if status:
            query = query.filter(status=status)
        if category:
            query = query.filter(category=category)
        
        certificates = await query.order_by('-created_at').all()
        
        result = []
        for cert in certificates:
            images = await CertificateImage.filter(
                certificate_id=cert.id
            ).order_by('image_order').all()
            
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
                } for img in images],
                "created_at": cert.created_at.isoformat() if cert.created_at else None
            })
        
        return result
    
    async def get_certificate_detail(self, certificate_id: int) -> Dict[str, Any]:
        """获取证书详情"""
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
    
    async def delete_certificate(self, certificate_id: int, deleted_by: str = None) -> Dict[str, Any]:
        """删除证书（软删除）"""
        certificate = await Certificate.get_or_none(id=certificate_id)
        if not certificate:
            return {"success": False, "error": "证书不存在"}
        
        certificate.is_valid = False
        certificate.invalid_reason = f"用户删除 - {deleted_by}"
        await certificate.save()
        
        self._log_data_trace("删除证书", {
            "certificate_id": certificate_id,
            "deleted_by": deleted_by
        })
        
        return {"success": True, "message": "证书已删除"}
    
    async def update_certificate_info(
        self,
        certificate_id: int,
        info: Dict[str, Any],
        updated_by: str = None
    ) -> Dict[str, Any]:
        """更新证书信息"""
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
        """获取学生证书统计"""
        total = await Certificate.filter(student_id=student_id, is_valid=True).count()
        approved = await Certificate.filter(student_id=student_id, is_valid=True, status="approved").count()
        pending = await Certificate.filter(student_id=student_id, is_valid=True, status="pending").count()
        rejected = await Certificate.filter(student_id=student_id, is_valid=True, status="rejected").count()
        
        category_stats = {}
        for cat in ['A', 'C1', 'C2', 'C3', 'C4']:
            if cat == 'A':
                count = await Certificate.filter(
                    student_id=student_id, is_valid=True, category='A', status="approved"
                ).count()
            else:
                count = await Certificate.filter(
                    student_id=student_id, is_valid=True, sub_category=cat, status="approved"
                ).count()
            category_stats[cat] = count
        
        total_score = await Certificate.filter(
            student_id=student_id, is_valid=True, status="approved"
        ).only('score')
        total_score_sum = sum(c.score for c in total_score)
        
        return {
            "student_id": student_id,
            "total_certificates": total,
            "approved_count": approved,
            "pending_count": pending,
            "rejected_count": rejected,
            "category_statistics": category_stats,
            "total_score": total_score_sum
        }


certificate_storage_service = CertificateStorageService()


def get_certificate_storage_service() -> CertificateStorageService:
    """获取证书存储服务实例"""
    return certificate_storage_service
