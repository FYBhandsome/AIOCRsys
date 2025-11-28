"""
文档管理器，负责管理向量数据库中的文档
"""

from typing import Dict, List, Optional, Any
import os
import uuid
from datetime import datetime
from pathlib import Path
import logging

# 导入向量数据库相关模块
from app.rag.vector_db import get_vector_db
from app.core.config_manager import settings


class DocumentManager:
    """文档管理器，负责管理向量数据库中的文档"""
    
    def __init__(self, collection_name: str = "documents"):
        """初始化文档管理器
        
        Args:
            collection_name: 向量数据库集合名称
        """
        self.collection_name = collection_name
        self.logger = logging.getLogger(__name__)
        
        # 初始化向量数据库
        try:
            self.vector_db = get_vector_db(collection_name)
            self.logger.info(f"向量数据库初始化成功，集合名称: {collection_name}")
        except Exception as e:
            self.logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    def add_document(self, file_path: str, name: str = None, description: str = None, 
                   category: str = None, enabled: bool = True) -> Dict[str, Any]:
        """添加文档到向量数据库
        
        Args:
            file_path: 文件路径
            name: 文档名称
            description: 文档描述
            category: 文档类别
            enabled: 是否启用
            
        Returns:
            文档信息字典
        """
        doc_id = str(uuid.uuid4())
        if not name:
            name = os.path.basename(file_path)
        
        # 读取文档内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"读取文档失败: {e}")
            raise
        
        # 准备文档元数据
        metadata = {
            "id": doc_id,
            "name": name,
            "file_path": file_path,
            "description": description,
            "category": category,
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
            "chunk_count": 1  # 初始为1，实际应该根据分块情况更新
        }
        
        # 添加到向量数据库
        try:
            document = {
                "text": content,
                "metadata": metadata
            }
            self.vector_db.add_documents([document])
            self.logger.info(f"文档已添加到向量数据库: {name}")
        except Exception as e:
            self.logger.error(f"添加文档到向量数据库失败: {e}")
            raise
        
        return metadata
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档信息
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档信息字典，如果不存在则返回None
        """
        try:
            # 从向量数据库查询文档
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if results and results["metadatas"] and len(results["metadatas"]) > 0:
                return results["metadatas"][0]
            else:
                return None
        except Exception as e:
            self.logger.error(f"获取文档信息失败: {e}")
            return None
    
    def list_documents(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """列出文档
        
        Args:
            enabled_only: 是否只列出启用的文档
            
        Returns:
            文档信息列表
        """
        try:
            # 从向量数据库获取所有文档
            results = self.vector_db.collection.get(include=["metadatas"])
            
            documents = []
            if results and results["metadatas"]:
                for metadata in results["metadatas"]:
                    # 如果只需要启用的文档，进行过滤
                    if not enabled_only or metadata.get("enabled", False):
                        documents.append(metadata)
            
            return documents
        except Exception as e:
            self.logger.error(f"列出文档失败: {e}")
            return []
    
    def update_document_status(self, doc_id: str, enabled: bool) -> bool:
        """更新文档状态
        
        Args:
            doc_id: 文档ID
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        try:
            # 从向量数据库获取文档
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not results or not results["metadatas"] or len(results["metadatas"]) == 0:
                self.logger.warning(f"文档不存在: {doc_id}")
                return False
            
            # 更新文档状态
            metadata = results["metadatas"][0]
            metadata["enabled"] = enabled
            
            # 更新向量数据库中的文档元数据
            self.vector_db.update_document_metadata(doc_id, metadata)
            
            if enabled:
                self.logger.info(f"文档已启用: {doc_id}")
            else:
                self.logger.info(f"文档已禁用: {doc_id}")
                
            return True
        except Exception as e:
            self.logger.error(f"更新文档状态失败: {e}")
            return False
    
    def update_document_chunks(self, doc_id: str, chunk_count: int) -> bool:
        """更新文档分块数量
        
        Args:
            doc_id: 文档ID
            chunk_count: 分块数量
            
        Returns:
            是否更新成功
        """
        try:
            # 从向量数据库获取文档
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not results or not results["metadatas"] or len(results["metadatas"]) == 0:
                self.logger.warning(f"文档不存在: {doc_id}")
                return False
            
            # 更新文档分块数量
            metadata = results["metadatas"][0]
            metadata["chunk_count"] = chunk_count
            
            # 更新向量数据库中的文档元数据
            self.vector_db.update_document_metadata(doc_id, metadata)
            
            self.logger.info(f"文档分块数量已更新: {doc_id} -> {chunk_count}")
            return True
        except Exception as e:
            self.logger.error(f"更新文档分块数量失败: {e}")
            return False
    
    def delete_document(self, doc_id: str, delete_file: bool = False) -> bool:
        """删除文档
        
        Args:
            doc_id: 文档ID
            delete_file: 是否删除文件
            
        Returns:
            是否删除成功
        """
        try:
            # 从向量数据库获取文档信息
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not results or not results["metadatas"] or len(results["metadatas"]) == 0:
                self.logger.warning(f"文档不存在: {doc_id}")
                return False
            
            metadata = results["metadatas"][0]
            file_path = metadata.get("file_path")
            
            # 从向量数据库删除文档
            self.vector_db.delete_documents_by_filter({"id": doc_id})
            
            # 如果需要，删除文件
            if delete_file and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"文件已删除: {file_path}")
                except Exception as e:
                    self.logger.error(f"删除文件失败: {e}")
            
            self.logger.info(f"文档已删除: {doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"删除文档失败: {e}")
            return False
    
    def get_enabled_documents(self) -> List[Dict[str, Any]]:
        """获取所有启用的文档
        
        Returns:
            启用的文档列表
        """
        try:
            # 从向量数据库获取所有文档
            results = self.vector_db.collection.get(include=["metadatas"])
            
            enabled_documents = []
            if results and results["metadatas"]:
                for metadata in results["metadatas"]:
                    # 只返回启用的文档
                    if metadata.get("enabled", False):
                        enabled_documents.append(metadata)
            
            return enabled_documents
        except Exception as e:
            self.logger.error(f"获取启用文档失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取文档统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 从向量数据库获取所有文档
            results = self.vector_db.collection.get(include=["metadatas"])
            
            total_documents = 0
            enabled_documents = 0
            total_chunks = 0
            
            if results and results["metadatas"]:
                total_documents = len(results["metadatas"])
                
                for metadata in results["metadatas"]:
                    if metadata.get("enabled", False):
                        enabled_documents += 1
                    
                    total_chunks += metadata.get("chunk_count", 0)
            
            return {
                "total_documents": total_documents,
                "enabled_documents": enabled_documents,
                "disabled_documents": total_documents - enabled_documents,
                "total_chunks": total_chunks
            }
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {
                "total_documents": 0,
                "enabled_documents": 0,
                "disabled_documents": 0,
                "total_chunks": 0
            }
    
    def reprocess_document(self, doc_id: str) -> bool:
        """重新处理文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否处理成功
        """
        try:
            # 从向量数据库获取文档
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas", "documents"]
            )
            
            if not results or not results["metadatas"] or len(results["metadatas"]) == 0:
                self.logger.warning(f"文档不存在: {doc_id}")
                return False
            
            metadata = results["metadatas"][0]
            file_path = metadata.get("file_path")
            
            if not file_path or not os.path.exists(file_path):
                self.logger.error(f"文档文件不存在: {file_path}")
                return False
            
            # 重新读取文档内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 这里可以添加文档预处理逻辑，如分块等
            # 简化实现，直接更新文档内容
            # 实际应用中，可能需要进行文本分块、向量化等操作
            
            # 更新向量数据库中的文档内容
            # 先删除旧文档
            self.vector_db.delete_documents_by_filter({"id": doc_id})
            
            # 添加新文档
            document = {
                "text": content,
                "metadata": metadata
            }
            self.vector_db.add_documents([document])
            
            self.logger.info(f"文档已重新处理: {doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"重新处理文档失败: {e}")
            return False