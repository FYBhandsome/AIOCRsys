"""
规则向量数据库实现 - 基于BaseVectorDB的具体实现
"""
from app.rag.vector_db.base_vector_db import BaseVectorDB
from app.core.config_manager import settings
from typing import List, Any, Dict, Optional
import logging


class RuleVectorDB(BaseVectorDB):
    """规则向量数据库（使用 Sentence-Transformers 嵌入）"""
    
    _instances = {}
    
    def __new__(cls, collection_name: str = "zongce_rules"):
        """
        单例模式实现，确保每个collection_name只有一个实例
        
        Args:
            collection_name: 集合名称
            
        Returns:
            RuleVectorDB实例
        """
        if collection_name not in cls._instances:
            instance = super(RuleVectorDB, cls).__new__(cls)
            cls._instances[collection_name] = instance
        return cls._instances[collection_name]
    
    def __init__(self, collection_name: str = "zongce_rules"):
        """
        初始化规则向量数据库
        
        Args:
            collection_name: 集合名称
        """
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        super().__init__(collection_name)
        self.logger = logging.getLogger(__name__)
        self._initialized = True
    
    def add_documents(self, documents: List[Any]):
        """
        添加文档到向量库
        
        Args:
            documents: 文档列表，支持LangChain Document或自定义字典格式
        """
        if not documents:
            self.logger.warning("没有文档需要添加到向量库")
            return
        
        try:
            # 获取当前集合中的最大ID，避免ID冲突
            existing_count = self.collection.count()
            
            # 准备文档
            texts, metadatas = self._prepare_documents_for_add(documents)
            ids = self._generate_document_ids(len(documents), existing_count)
            
            # 添加文档
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"已添加 {len(documents)} 个文档片段到向量库")
        except Exception as e:
            self.logger.error(f"添加文档到向量库失败: {e}")
            raise
    
    def search_relevant(self, query: str, top_k: int = None, metadata_filter: Optional[Dict] = None):
        """
        检索相关规则
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
            metadata_filter: 元数据过滤条件，例如 {"type": "competition"} 或 {"category": "A类"}
            
        Returns:
            检索结果，包含文档、元数据和距离
        """
        if top_k is None:
            top_k = settings.TOP_K
        
        try:
            # 构建查询参数
            query_params = self._build_query_params(query, top_k, metadata_filter)
            
            # 执行查询
            results = self.collection.query(**query_params)
            
            return self._process_query_results(results)
        except Exception as e:
            self.logger.error(f"检索相关规则失败: {e}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": []
            }
    
    def search_competition_category(self, competition_name: str, top_k: int = 5):
        """
        搜索竞赛所属类别
        
        Args:
            competition_name: 竞赛名称
            top_k: 返回的结果数量
            
        Returns:
            竞赛类别信息
        """
        self.logger.info(f"搜索竞赛类别: {competition_name}")
        
        # 只在竞赛列表中搜索
        return self.search_relevant(
            query=competition_name,
            top_k=top_k,
            metadata_filter={"type": "competition"}
        )
    
    def search_category_score(self, category: str, top_k: int = 1):
        """
        搜索类别对应的分数
        
        Args:
            category: 竞赛类别
            top_k: 返回的结果数量
            
        Returns:
            类别分数信息
        """
        self.logger.info(f"搜索类别分数: {category}")
        
        # 只在规则中搜索，使用$and操作符组合多个条件
        return self.search_relevant(
            query=f"{category}比赛",
            top_k=top_k,
            metadata_filter={"$and": [
                {"type": "rule"},
                {"category": category}
            ]}
        )
    
    def clear_all_documents(self):
        """清空所有文档"""
        try:
            # 获取所有文档的ID
            count = self.collection.count()
            if count > 0:
                # 获取所有ID
                all_data = self.collection.get()
                if all_data and 'ids' in all_data and all_data['ids']:
                    self.collection.delete(ids=all_data['ids'])
                    self.logger.info(f"已删除 {len(all_data['ids'])} 个文档")
                else:
                    self.logger.warning("集合为空，无需删除")
            else:
                self.logger.warning("集合为空，无需删除")
        except Exception as e:
            self.logger.error(f"清空文档失败: {e}")
            # 如果失败，尝试删除并重新创建集合
            try:
                self.client.delete_collection(name=self.collection_name)
                self.collection = self._get_or_create_collection(self.client)
                self.logger.info("已重新创建集合")
            except Exception as e2:
                self.logger.error(f"重新创建集合失败: {e2}")
                raise
    
    def update_document_metadata(self, doc_id: str, new_metadata: Dict[str, Any]):
        """
        更新文档的元数据
        
        Args:
            doc_id: 文档ID
            new_metadata: 新的元数据
        """
        try:
            self.collection.update(
                ids=[doc_id],
                metadatas=[new_metadata]
            )
            self.logger.info(f"已更新文档 {doc_id} 的元数据")
        except Exception as e:
            self.logger.error(f"更新文档元数据失败: {e}")
            raise
    
    def delete_documents_by_filter(self, metadata_filter: Dict[str, Any]):
        """
        根据元数据过滤条件删除文档
        
        Args:
            metadata_filter: 元数据过滤条件
        """
        try:
            # 获取符合条件的文档ID
            filtered_docs = self.collection.get(where=metadata_filter)
            
            if filtered_docs and 'ids' in filtered_docs and filtered_docs['ids']:
                self.collection.delete(ids=filtered_docs['ids'])
                self.logger.info(f"已根据过滤条件删除 {len(filtered_docs['ids'])} 个文档")
            else:
                self.logger.warning("没有找到符合条件的文档")
        except Exception as e:
            self.logger.error(f"根据过滤条件删除文档失败: {e}")
            raise
    
    def get_document_by_id(self, doc_id: str):
        """
        根据ID获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档内容
        """
        try:
            result = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
            
            if result and 'documents' in result and result['documents']:
                return {
                    "id": doc_id,
                    "content": result['documents'][0],
                    "metadata": result['metadatas'][0] if result['metadatas'] else {}
                }
            else:
                self.logger.warning(f"未找到ID为 {doc_id} 的文档")
                return None
        except Exception as e:
            self.logger.error(f"获取文档失败: {e}")
            raise
    
    def update_document_metadata(self, doc_id: str, metadata: Dict[str, Any]):
        """
        更新文档元数据
        
        Args:
            doc_id: 文档ID
            metadata: 新的元数据
        """
        try:
            # ChromaDB 不支持直接更新元数据，需要先删除再添加
            # 获取原文档内容
            result = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
            
            if result and 'documents' in result and result['documents']:
                # 删除原文档
                self.collection.delete(ids=[doc_id])
                
                # 重新添加文档
                self.collection.add(
                    ids=[doc_id],
                    documents=[result['documents'][0]],
                    metadatas=[metadata]
                )
                self.logger.info(f"文档元数据已更新: {doc_id}")
            else:
                self.logger.warning(f"未找到ID为 {doc_id} 的文档")
        except Exception as e:
            self.logger.error(f"更新文档元数据失败: {e}")
            raise


def get_vector_db(collection_name: str = "zongce_rules") -> RuleVectorDB:
    """
    获取向量数据库单例实例的便捷函数
    
    Args:
        collection_name: 集合名称，默认为"zongce_rules"
        
    Returns:
        RuleVectorDB单例实例
    """
    return RuleVectorDB(collection_name)

