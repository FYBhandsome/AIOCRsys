"""
文档服务层
处理文档管理的业务逻辑
"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import UploadFile
from app.core.document_manager import DocumentManager
from app.core.logger import get_logger, LogContext, track_performance

logger = get_logger(__name__)


class DocumentService:
    """文档服务类"""
    
    def __init__(self):
        """初始化文档服务"""
        self.logger = get_logger(__name__)
        self.document_manager = DocumentManager()
        self.logger.info("文档服务初始化完成")
    
    @track_performance("upload_document")
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
        with LogContext(self.logger, "上传文档", {"filename": file.filename, "category": category}):
            try:
                try:
                    tags_list = json.loads(tags) if tags else []
                except json.JSONDecodeError:
                    tags_list = []
                    self.logger.warning(f"标签解析失败，使用空列表: {tags}")
                
                upload_dir = Path("data/uploads") / category
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                file_path = upload_dir / file.filename
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                file_size = file_path.stat().st_size
                self.logger.debug(f"文件保存成功: {file_path}, 大小: {file_size}字节")
                
                doc_info = self.document_manager.add_document(
                    file_path=str(file_path),
                    name=file.filename,
                    description=description,
                    category=category,
                    enabled=True
                )
                
                self.logger.info(
                    f"文档上传成功: {file.filename}",
                    extra={'params': {'doc_id': doc_info['id'], 'file_size': file_size}}
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
                self.logger.error(f"文档上传失败: {str(e)}", exc_info=True)
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
        self.logger.debug(f"获取文档列表: category={category}, tags={tags}")
        try:
            tags_list = []
            if tags:
                try:
                    tags_list = json.loads(tags)
                except json.JSONDecodeError:
                    tags_list = tags.split(",")
            
            documents = self.document_manager.list_documents(enabled_only=False)
            
            if category:
                documents = [doc for doc in documents if doc.get("category") == category]
            
            self.logger.info(f"获取文档列表完成: {len(documents)}条记录")
            return {
                "documents": documents,
                "total": len(documents)
            }
            
        except Exception as e:
            self.logger.error(f"获取文档列表失败: {str(e)}", exc_info=True)
            raise
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档详情
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档信息字典，如果不存在则返回None
        """
        self.logger.debug(f"获取文档详情: document_id={document_id}")
        try:
            return self.document_manager.get_document(document_id)
        except Exception as e:
            self.logger.error(f"获取文档详情失败: {str(e)}", exc_info=True)
            raise
    
    @track_performance("delete_document_service")
    def delete_document(self, document_id: str) -> bool:
        """删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否删除成功
        """
        self.logger.info(f"删除文档: document_id={document_id}")
        try:
            result = self.document_manager.delete_document(document_id, delete_file=True)
            if result:
                self.logger.info(f"文档删除成功: {document_id}")
            return result
        except Exception as e:
            self.logger.error(f"文档删除失败: {str(e)}", exc_info=True)
            raise
    
    def update_document_status(self, document_id: str, enabled: bool) -> bool:
        """更新文档状态
        
        Args:
            document_id: 文档ID
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        self.logger.info(f"更新文档状态: document_id={document_id}, enabled={enabled}")
        try:
            return self.document_manager.update_document_status(document_id, enabled)
        except Exception as e:
            self.logger.error(f"更新文档状态失败: {str(e)}", exc_info=True)
            raise
    
    def get_document_processing_status(self, document_id: str) -> Dict[str, Any]:
        """获取文档处理状态
        
        Args:
            document_id: 文档ID
            
        Returns:
            处理状态字典
        """
        self.logger.debug(f"获取文档处理状态: document_id={document_id}")
        try:
            document = self.document_manager.get_document(document_id)
            
            if not document:
                self.logger.warning(f"文档不存在: {document_id}")
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
