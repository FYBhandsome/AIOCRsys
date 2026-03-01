"""
基础向量数据库类 - 提取公共代码，减少重复
实现懒加载模式，加快启动速度
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
    _embedding_func_cache = None
    
    def __init__(self, collection_name: str = "zongce_rules"):
        """
        初始化基础向量数据库（懒加载模式）
        
        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self.logger = logging.getLogger(__name__)
        
        self._embedding_func = None
        self._embedding_loaded = False
        self.client = None
        self.collection = None
        
        try:
            os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
        except Exception as e:
            self.logger.warning(f"环境配置失败: {e}")
        
        try:
            self.client = self._create_client()
        except Exception as e:
            self.logger.error(f"创建Chroma客户端失败: {e}")
            return
        
        try:
            self.collection = self._get_collection_lazy()
        except Exception as e:
            self.logger.error(f"获取集合失败: {e}")
            self.logger.error(traceback.format_exc())
    
    @property
    def embedding_func(self):
        """懒加载嵌入函数"""
        if not self._embedding_loaded:
            self._embedding_func = self._load_embedding_function()
            self._embedding_loaded = True
        return self._embedding_func
    
    @embedding_func.setter
    def embedding_func(self, value):
        self._embedding_func = value
        self._embedding_loaded = True
    
    def _load_embedding_function(self):
        """
        加载嵌入函数（懒加载）
        使用缓存避免重复加载
        """
        if BaseVectorDB._embedding_func_cache is not None:
            self.logger.info("使用缓存的嵌入模型")
            return BaseVectorDB._embedding_func_cache
        
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
            
            func = SentenceTransformerEmbeddingFunction(
                model_name=settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE,
                trust_remote_code=True
            )
            self.logger.info("嵌入模型加载完成!")
            BaseVectorDB._embedding_func_cache = func
            return func
        except Exception as e:
            self.logger.warning(f"加载嵌入模型失败: {e}")
            return self._load_fallback_embedding()
    
    def _load_fallback_embedding(self):
        """加载备用嵌入函数"""
        try:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            
            func = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2",
                device="cpu",
                trust_remote_code=True
            )
            self.logger.info("使用备用嵌入模型 all-MiniLM-L6-v2")
            BaseVectorDB._embedding_func_cache = func
            return func
        except Exception as e2:
            self.logger.error(f"初始化备用嵌入函数也失败: {e2}")
            self.logger.warning("嵌入函数初始化失败，将在运行时重试")
            return None
    
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
    
    def _get_collection_lazy(self, collection_name=None):
        """
        获取集合（懒加载模式）
        启动时不加载嵌入函数，只在需要时加载
        """
        name = collection_name or self.collection_name
        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"集合 '{name}' 加载完成，文档数: {collection.count()}")
            return collection
        except Exception as e:
            self.logger.error(f"获取集合失败: {e}")
            raise
    
    def _ensure_embedding_func(self):
        """确保嵌入函数已加载"""
        if self._embedding_func is None and not self._embedding_loaded:
            self._embedding_func = self._load_embedding_function()
            self._embedding_loaded = True
        return self._embedding_func
    
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
            result = {}
            for k, v in metadata.items():
                if v is None:
                    continue
                elif isinstance(v, (str, int, float, bool)):
                    result[k] = v
                elif isinstance(v, list):
                    result[k] = ', '.join(str(item) for item in v)
                elif isinstance(v, dict):
                    result[k] = str(v)
                else:
                    result[k] = str(v)
            return result
        
        texts = []
        metadatas = []
        
        for doc in documents:
            if hasattr(doc, 'page_content'):
                texts.append(doc.page_content)
                metadata = getattr(doc, 'metadata', {}) or {}
                metadatas.append(sanitize_metadata(metadata))
            elif isinstance(doc, dict):
                text = doc.get('content') or doc.get('text') or doc.get('page_content', '')
                texts.append(text)
                metadata = doc.get('metadata', {}) or {}
                metadatas.append(sanitize_metadata(metadata))
            else:
                texts.append(str(doc))
                metadatas.append({})
        
        return texts, metadatas
    
    def _generate_document_ids(self, count: int, start_index: int = 0) -> List[str]:
        """生成文档ID"""
        import uuid
        return [str(uuid.uuid4()) for _ in range(count)]
    
    def count(self) -> int:
        """获取文档数量"""
        if self.collection is None:
            return 0
        return self.collection.count()
