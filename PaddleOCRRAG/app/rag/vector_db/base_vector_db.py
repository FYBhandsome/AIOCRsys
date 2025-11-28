"""
基础向量数据库类 - 提取公共代码，减少重复
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.core.config_manager import settings
from typing import List, Any, Dict, Optional, Tuple
import os
import logging


class BaseVectorDB:
    """向量数据库基础类，提供公共功能"""
    
    def __init__(self, collection_name: str = "zongce_rules"):
        """
        初始化基础向量数据库
        
        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self.logger = logging.getLogger(__name__)
        
        # 设置 Hugging Face 镜像（加速国内下载）
        os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
        
        # 确保数据库目录存在
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
        
        # 初始化嵌入函数（只需一次）
        self._init_embedding_function()
        
        # 初始化Chroma客户端
        self.client = self._create_client()
        
        # 获取或创建集合
        self.collection = self._get_or_create_collection(self.client)
    
    def _init_embedding_function(self):
        """初始化嵌入函数"""
        try:
            # 使用 Sentence-Transformers 嵌入函数（轻量级，384维向量）
            self.logger.info(f"正在加载嵌入模型: {settings.EMBEDDING_MODEL}...")
            
            # 设置超时和重试参数
            import os
            os.environ["TRANSFORMERS_OFFLINE"] = "0"  # 允许在线下载
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"  # 禁用遥测
            
            self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE
            )
            self.logger.info("嵌入模型加载完成!")
        except Exception as e:
            self.logger.warning(f"加载嵌入模型失败，使用默认嵌入函数: {e}")
            # 使用默认的嵌入函数作为后备
            try:
                self.embedding_func = embedding_functions.DefaultEmbeddingFunction()
                self.logger.info("使用默认嵌入函数")
            except Exception as e2:
                self.logger.error(f"初始化默认嵌入函数也失败: {e2}")
                # 最后的后备方案：使用OpenAI嵌入（如果可用）
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
            # 如果嵌入函数为None，尝试重新初始化
            if self.embedding_func is None:
                self.logger.info("尝试重新初始化嵌入函数...")
                self._init_embedding_function()
            
            # 如果仍然为None，使用默认配置
            embedding_func = self.embedding_func
            if embedding_func is None:
                self.logger.warning("使用无嵌入函数模式创建集合")
                embedding_func = None
            
            return client.get_or_create_collection(
                name=name,
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            self.logger.error(f"获取或创建集合失败: {e}")
            # 尝试不使用嵌入函数创建集合
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
        
        # 支持两种格式的文档：LangChain Document 和自定义字典
        if hasattr(documents[0], 'page_content'):
            # LangChain Document 格式
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
        else:
            # 自定义字典格式
            texts = [doc["text"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
        
        return texts, metadatas
    
    def _generate_document_ids(self, count: int, existing_count: int = 0) -> List[str]:
        """生成文档ID"""
        return [f"doc_{existing_count + i}" for i in range(count)]
    
    def _process_query_results(self, results) -> Dict[str, Any]:
        """处理查询结果，统一返回格式"""
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
    
    def _build_query_params(self, query: str, top_k: int, metadata_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """构建查询参数"""
        query_params = {
            "query_texts": [query],
            "n_results": top_k
        }
        
        # 添加元数据过滤条件
        if metadata_filter:
            query_params["where"] = metadata_filter
            
        return query_params
    
    def _calculate_db_stats(self, collection) -> Dict[str, Any]:
        """计算数据库统计信息"""
        try:
            count = collection.count()
            
            # 获取所有元数据类型统计
            all_data = collection.get(include=["metadatas"])
            type_stats = {}
            category_stats = {}
            
            if all_data and 'metadatas' in all_data and all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    # 统计类型
                    doc_type = metadata.get('type', 'unknown')
                    type_stats[doc_type] = type_stats.get(doc_type, 0) + 1
                    
                    # 统计类别
                    category = metadata.get('category', 'unknown')
                    category_stats[category] = category_stats.get(category, 0) + 1
            
            return {
                "total_documents": count,
                "type_stats": type_stats,
                "category_stats": category_stats,
                "embedding_model": settings.EMBEDDING_MODEL,
                "status": "ready"
            }
        except Exception as e:
            self.logger.error(f"计算数据库统计信息失败: {e}")
            return {
                "total_documents": 0,
                "type_stats": {},
                "category_stats": {},
                "embedding_model": settings.EMBEDDING_MODEL,
                "status": "error",
                "error": str(e)
            }
    
    # 公共接口方法
    def add_documents(self, documents: List[Any]):
        """添加文档到向量库 - 子类应重写此方法"""
        raise NotImplementedError("子类必须实现add_documents方法")
    
    def search_relevant(self, query: str, top_k: int = None, metadata_filter: Optional[Dict] = None):
        """检索相关规则 - 子类应重写此方法"""
        raise NotImplementedError("子类必须实现search_relevant方法")
    
    def get_db_stats(self) -> Dict[str, Any]:
        """获取向量数据库统计信息"""
        return self._calculate_db_stats(self.collection)
    
    def clear_all_documents(self):
        """清空所有文档 - 子类应重写此方法"""
        raise NotImplementedError("子类必须实现clear_all_documents方法")