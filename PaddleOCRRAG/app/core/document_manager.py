"""
文档管理器，负责管理向量数据库中的文档
"""

from typing import Dict, List, Optional, Any
import os
import uuid
from datetime import datetime
from pathlib import Path

from app.rag.vector_db import get_vector_db
from app.core.config_manager import settings
from app.core.logger import get_logger, LogContext, track_performance

logger = get_logger(__name__)


def extract_text_from_file(file_path: str) -> str:
    """从文件中提取文本内容，支持多种格式

    Args:
        file_path: 文件路径

    Returns:
        提取的文本内容
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    try:
        if suffix == '.docx':
            try:
                import docx2txt
                text = docx2txt.process(file_path)
                return text if text else ""
            except ImportError:
                logger.warning("docx2txt未安装，尝试使用python-docx")
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = "\n".join([para.text for para in doc.paragraphs])
                    return text
                except ImportError:
                    raise ImportError("需要安装 docx2txt 或 python-docx 来处理.docx文件")

        elif suffix == '.xlsx':
            try:
                import pandas as pd
                df = pd.read_excel(file_path)
                texts = []
                for idx, row in df.iterrows():
                    row_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
                    if row_text.strip():
                        texts.append(row_text)
                return '\n'.join(texts)
            except ImportError:
                raise ImportError("需要安装 pandas 和 openpyxl 来处理.xlsx文件")

        elif suffix == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                raise ImportError("需要安装 PyPDF2 来处理.pdf文件")

        elif suffix == '.txt' or suffix == '.md' or suffix == '.csv':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        else:
            # 默认尝试以UTF-8文本模式读取
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

    except Exception as e:
        logger.error(f"提取文件文本失败: {file_path}, 错误: {e}")
        raise


class DocumentManager:
    """文档管理器，负责管理向量数据库中的文档"""
    
    def __init__(self, collection_name: str = "zongce_rules"):
        """初始化文档管理器
        
        Args:
            collection_name: 向量数据库集合名称
        """
        self.collection_name = collection_name
        self.logger = get_logger(__name__)
        
        with LogContext(self.logger, "初始化文档管理器", {"collection_name": collection_name}):
            try:
                self.vector_db = get_vector_db(collection_name)
                self.logger.info(f"向量数据库初始化成功，集合名称: {collection_name}")
            except Exception as e:
                self.logger.error(f"向量数据库初始化失败: {e}", exc_info=True)
                raise
    
    @track_performance("add_document")
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
        with LogContext(self.logger, "添加文档", {"file_path": file_path, "name": name}):
            doc_id = str(uuid.uuid4())
            if not name:
                name = os.path.basename(file_path)
            
            try:
                content = extract_text_from_file(file_path)
                self.logger.debug(f"文档内容读取成功: {len(content)} 字符")
            except Exception as e:
                self.logger.error(f"读取文档失败: {e}", exc_info=True)
                raise
            
            metadata = {
                "id": doc_id,
                "name": name,
                "file_path": file_path,
                "description": description,
                "category": category,
                "enabled": enabled,
                "created_at": datetime.now().isoformat(),
                "chunk_count": 1
            }
            
            try:
                document = {
                    "text": content,
                    "metadata": metadata
                }
                self.vector_db.add_documents([document])
                self.logger.info(f"文档已添加到向量数据库: {name}", extra={'params': {'doc_id': doc_id}})
            except Exception as e:
                self.logger.error(f"添加文档到向量数据库失败: {e}", exc_info=True)
                raise
            
            return metadata
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档信息
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档信息字典，如果不存在则返回None
        """
        self.logger.debug(f"获取文档: doc_id={doc_id}")
        try:
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if results and results["metadatas"] and len(results["metadatas"]) > 0:
                return results["metadatas"][0]
            else:
                self.logger.warning(f"文档不存在: {doc_id}")
                return None
        except Exception as e:
            self.logger.error(f"获取文档信息失败: {e}", exc_info=True)
            return None
    
    def list_documents(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """列出文档
        
        Args:
            enabled_only: 是否只列出启用的文档
            
        Returns:
            文档信息列表
        """
        self.logger.debug(f"列出文档: enabled_only={enabled_only}")
        try:
            results = self.vector_db.collection.get(include=["metadatas"])
            
            documents = []
            if results and results["metadatas"]:
                for metadata in results["metadatas"]:
                    if not enabled_only or metadata.get("enabled", False):
                        documents.append(metadata)
            
            self.logger.info(f"列出文档完成: {len(documents)}条记录")
            return documents
        except Exception as e:
            self.logger.error(f"列出文档失败: {e}", exc_info=True)
            return []
    
    def update_document_status(self, doc_id: str, enabled: bool) -> bool:
        """更新文档状态
        
        Args:
            doc_id: 文档ID
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        self.logger.info(f"更新文档状态: doc_id={doc_id}, enabled={enabled}")
        try:
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not results or not results["metadatas"] or len(results["metadatas"]) == 0:
                self.logger.warning(f"文档不存在: {doc_id}")
                return False
            
            metadata = results["metadatas"][0]
            metadata["enabled"] = enabled
            
            self.vector_db.update_document_metadata(doc_id, metadata)
            
            status = "启用" if enabled else "禁用"
            self.logger.info(f"文档已{status}: {doc_id}", extra={'params': {'enabled': enabled}})
            return True
        except Exception as e:
            self.logger.error(f"更新文档状态失败: {e}", exc_info=True)
            return False
    
    def update_document_chunks(self, doc_id: str, chunk_count: int) -> bool:
        """更新文档分块数量
        
        Args:
            doc_id: 文档ID
            chunk_count: 分块数量
            
        Returns:
            是否更新成功
        """
        self.logger.debug(f"更新文档分块数量: doc_id={doc_id}, chunk_count={chunk_count}")
        try:
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not results or not results["metadatas"] or len(results["metadatas"]) == 0:
                self.logger.warning(f"文档不存在: {doc_id}")
                return False
            
            metadata = results["metadatas"][0]
            metadata["chunk_count"] = chunk_count
            
            self.vector_db.update_document_metadata(doc_id, metadata)
            
            self.logger.info(f"文档分块数量已更新: {doc_id} -> {chunk_count}")
            return True
        except Exception as e:
            self.logger.error(f"更新文档分块数量失败: {e}", exc_info=True)
            return False
    
    @track_performance("delete_document")
    def delete_document(self, doc_id: str, delete_file: bool = False) -> bool:
        """删除文档
        
        Args:
            doc_id: 文档ID
            delete_file: 是否删除文件
            
        Returns:
            是否删除成功
        """
        self.logger.info(f"删除文档: doc_id={doc_id}, delete_file={delete_file}")
        try:
            results = self.vector_db.collection.get(
                ids=[doc_id],
                include=["metadatas"]
            )
            
            if not results or not results["metadatas"] or len(results["metadatas"]) == 0:
                self.logger.warning(f"文档不存在: {doc_id}")
                return False
            
            metadata = results["metadatas"][0]
            file_path = metadata.get("file_path")
            
            self.vector_db.delete_documents_by_filter({"id": doc_id})
            
            if delete_file and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"文件已删除: {file_path}")
                except Exception as e:
                    self.logger.error(f"删除文件失败: {e}", exc_info=True)
            
            self.logger.info(f"文档已删除: {doc_id}", extra={'params': {'delete_file': delete_file}})
            return True
        except Exception as e:
            self.logger.error(f"删除文档失败: {e}", exc_info=True)
            return False
    
    def get_enabled_documents(self) -> List[Dict[str, Any]]:
        """获取所有启用的文档
        
        Returns:
            启用的文档列表
        """
        self.logger.debug("获取所有启用的文档")
        try:
            results = self.vector_db.collection.get(include=["metadatas"])
            
            enabled_documents = []
            if results and results["metadatas"]:
                for metadata in results["metadatas"]:
                    if metadata.get("enabled", False):
                        enabled_documents.append(metadata)
            
            self.logger.debug(f"找到 {len(enabled_documents)} 个启用的文档")
            return enabled_documents
        except Exception as e:
            self.logger.error(f"获取启用文档失败: {e}", exc_info=True)
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取文档统计信息
        
        Returns:
            统计信息字典
        """
        self.logger.debug("获取文档统计信息")
        try:
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
            content = extract_text_from_file(file_path)
            
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