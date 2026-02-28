"""
基础向量数据库类 - 提取公共代码，减少重复
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config_manager import settings
from typing import List, Any, Dict, Optional, Tuple
import os
import logging
import traceback


class BaseVectorDB:
    """向量数据库基础类，提供公共功能"""
    
    _initialized_collections = set()
    
    def __init__(self, collection_name: str = "zongce_rules"):
        """
        初始化基础向量数据库
        
        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self.logger = logging.getLogger(__name__)
        
        self.embedding_func = None
        self.client = None
        self.collection = None
        
        try:
            os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"环境配置失败: {e}")
        
        try:
            self._init_embedding_function()
        except Exception as e:
            self.logger.warning(f"嵌入函数初始化失败: {e}")
            self.embedding_func = None
        
        try:
            self.client = self._create_client()
        except Exception as e:
            self.logger.error(f"创建Chroma客户端失败: {e}")
            return
        
        try:
            self.collection = self._get_or_create_collection(self.client)
        except Exception as e:
            self.logger.error(f"获取或创建集合失败: {e}")
            self.logger.error(traceback.format_exc())
    
    def _init_embedding_function(self):
        """初始化嵌入函数"""
        try:
            self.logger.info(f"正在加载嵌入模型: {settings.EMBEDDING_MODEL}...")
            
            os.environ["TRANSFORMERS_OFFLINE"] = "0"
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
            os.environ["CURL_CA_BUNDLE"] = ""
            os.environ["REQUESTS_CA_BUNDLE"] = ""
            os.environ["SSL_CERT_FILE"] = ""
            
            import ssl
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:
                pass
            
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            
            self.embedding_func = SentenceTransformerEmbeddingFunction(
                model_name=settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE,
                trust_remote_code=True
            )
            self.logger.info("嵌入模型加载完成!")
        except Exception as e:
            self.logger.warning(f"加载嵌入模型失败: {e}")
            try:
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                
                from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
                
                self.embedding_func = SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2",
                    device="cpu",
                    trust_remote_code=True
                )
                self.logger.info("使用备用嵌入模型 all-MiniLM-L6-v2")
            except Exception as e2:
                self.logger.error(f"初始化备用嵌入函数也失败: {e2}")
                self.embedding_func = None
                self.logger.warning("嵌入函数初始化失败，将在运行时重试")
    
    def _create_client(self):
        """创建Chroma客户端"""
        try:
            return chromadb.PersistentClient(
                path=settings.CHROMA_DB_PATH,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        except Exception as e:
            self.logger.error(f"创建Chroma客户端失败: {e}")
            raise
    
    def _get_or_create_collection(self, client, collection_name=None):
        """获取或创建集合"""
        name = collection_name or self.collection_name
        try:
            if self.embedding_func is None:
                self.logger.info("尝试重新初始化嵌入函数...")
                self._init_embedding_function()
            
            embedding_func = self.embedding_func
            if embedding_func is None:
                self.logger.warning("使用无嵌入函数模式创建集合")
            
            return client.get_or_create_collection(
                name=name,
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            self.logger.error(f"获取或创建集合失败: {e}")
            try:
                self.logger.info("尝试创建无嵌入函数的集合...")
                return client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e2:
                self.logger.error(f"创建无嵌入函数集合也失败: {e2}")
                raise
    
    def _prepare_documents_for_add(self, documents: List[Any]) -> Tuple[List[str], List[Dict]]:
        """
        准备要添加的文档
        
        Args:
            documents: 文档列表
            
        Returns:
            元组 (texts, metadatas)
        """
        if not documents:
            return [], []
        
        def sanitize_metadata(metadata: Dict) -> Dict:
            """清理元数据，确保所有值都是基本类型"""
            sanitized = {}
            for key, value in metadata.items():
                if value is None:
                    sanitized[key] = ""
                elif isinstance(value, (str, int, float, bool)):
                    sanitized[key] = value
                else:
                    sanitized[key] = str(value)
            return sanitized
        
        texts = []
        metadatas = []
        
        for doc in documents:
            if hasattr(doc, 'page_content'):
                texts.append(doc.page_content)
                metadata = getattr(doc, 'metadata', {})
                metadatas.append(sanitize_metadata(metadata))
            elif isinstance(doc, dict):
                texts.append(doc.get('content', doc.get('text', str(doc))))
                metadatas.append(sanitize_metadata(doc.get('metadata', {})))
            else:
                texts.append(str(doc))
                metadatas.append({})
        
        return texts, metadatas
    
    def _generate_document_ids(self, count: int, existing_count: int = 0) -> List[str]:
        """
        生成文档ID
        
        Args:
            count: 需要生成的ID数量
            existing_count: 现有文档数量
            
        Returns:
            ID列表
        """
        import uuid
        return [f"doc_{existing_count + i}_{uuid.uuid4().hex[:8]}" for i in range(count)]
    
    def add_documents(self, documents: List[Any]) -> int:
        """
        添加文档到向量库
        
        Args:
            documents: 文档列表
            
        Returns:
            添加的文档数量
        """
        if not documents:
            return 0
        
        if self.collection is None:
            self.logger.error("集合未初始化")
            return 0
        
        try:
            texts, metadatas = self._prepare_documents_for_add(documents)
            existing_count = self.collection.count()
            ids = self._generate_document_ids(len(texts), existing_count)
            
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return len(texts)
        except Exception as e:
            self.logger.error(f"添加文档失败: {e}")
            return 0
    
    def search(self, query: str, n_results: int = 5, where: Dict = None) -> Dict:
        """
        搜索文档
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件
            
        Returns:
            搜索结果
        """
        if self.collection is None:
            self.logger.error("集合未初始化")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            return results
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}
    
    def count(self) -> int:
        """获取文档数量"""
        if self.collection is None:
            return 0
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"获取文档数量失败: {e}")
            return 0
    
    def delete_collection(self):
        """删除集合"""
        if self.client and self.collection_name:
            try:
                self.client.delete_collection(self.collection_name)
                self.logger.info(f"集合 {self.collection_name} 已删除")
            except Exception as e:
                self.logger.error(f"删除集合失败: {e}")
