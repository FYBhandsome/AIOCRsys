"""
文档服务层
处理文档管理的业务逻辑
"""
import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import UploadFile
from app.core.document_manager import DocumentManager

logger = logging.getLogger(__name__)


class DocumentService:
    """文档服务类"""
    
    def __init__(self):
        """初始化文档服务"""
        self.document_manager = DocumentManager()
    
    def upload_document(self, file: UploadFile, category: str, 
                       tags: str = "[]", description: str = "") -> Dict[str, Any]:
        """上传文档
        
        Args:
            file: 上传的文件
            category: 文档类别
            tags: 标签（JSON字符串）
            description: 描述
            
        Returns:
            上传结果字典
        """
        try:
            # 解析标签
            try:
                tags_list = json.loads(tags) if tags else []
            except json.JSONDecodeError:
                tags_list = []
            
            # 创建上传目录
            upload_dir = Path("data/uploads") / category
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 获取文件大小
            file_size = file_path.stat().st_size
            
            # 使用document_manager添加文档记录
            doc_info = self.document_manager.add_document(
                file_path=str(file_path),
                name=file.filename,
                description=description,
                category=category,
                enabled=True
            )
            
            return {
                "document_id": doc_info["id"],
                "filename": file.filename,
                "category": category,
                "tags": tags_list,
                "description": description,
                "file_size": file_size,
                "processed": False,
                "uploaded_at": doc_info["created_at"]
            }
            
        except Exception as e:
            logger.error(f"文档上传失败: {str(e)}")
            raise
    
    def list_documents(self, category: Optional[str] = None, 
                      tags: Optional[str] = None) -> Dict[str, Any]:
        """获取文档列表
        
        Args:
            category: 文档类别过滤
            tags: 标签过滤
            
        Returns:
            文档列表字典
        """
        try:
            # 解析标签
            tags_list = []
            if tags:
                try:
                    tags_list = json.loads(tags)
                except json.JSONDecodeError:
                    tags_list = tags.split(",")
            
            # 使用document_manager获取文档列表
            documents = self.document_manager.list_documents(enabled_only=False)
            
            # 如果指定了category，进行过滤
            if category:
                documents = [doc for doc in documents if doc.get("category") == category]
            
            return {
                "documents": documents,
                "total": len(documents)
            }
            
        except Exception as e:
            logger.error(f"获取文档列表失败: {str(e)}")
            raise
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档详情
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档信息字典，如果不存在则返回None
        """
        try:
            return self.document_manager.get_document(document_id)
        except Exception as e:
            logger.error(f"获取文档详情失败: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否删除成功
        """
        try:
            return self.document_manager.delete_document(document_id, delete_file=True)
        except Exception as e:
            logger.error(f"文档删除失败: {str(e)}")
            raise
    
    def update_document_status(self, document_id: str, enabled: bool) -> bool:
        """更新文档状态
        
        Args:
            document_id: 文档ID
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        try:
            return self.document_manager.update_document_status(document_id, enabled)
        except Exception as e:
            logger.error(f"更新文档状态失败: {str(e)}")
            raise
    
    def get_document_processing_status(self, document_id: str) -> Dict[str, Any]:
        """获取文档处理状态
        
        Args:
            document_id: 文档ID
            
        Returns:
            处理状态字典
        """
        try:
            document = self.document_manager.get_document(document_id)
            
            if not document:
                raise ValueError("文档不存在")
            
            return {
                "document_id": document["id"],
                "document_name": document["name"],
                "status": "processed" if document["enabled"] else "disabled",
                "chunks_count": document.get("chunks_count", 0),
                "created_at": document["created_at"],
                "enabled": document["enabled"]
            }
            
        except Exception as e:
            logger.error(f"获取文档处理状态失败: {str(e)}")
            raise
