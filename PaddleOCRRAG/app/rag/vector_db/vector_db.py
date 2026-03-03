"""
规则向量数据库实现 - 基于BaseVectorDB的具体实现
支持类别感知检索和重排
优化检索算法：相似度阈值过滤、重排序权重优化
"""
import time
from app.rag.vector_db.base_vector_db import BaseVectorDB
from app.core.config_manager import settings
from typing import List, Any, Dict, Optional, Tuple

from app.rag.preprocessors.intent_recognizer import IntentResult, get_intent_recognizer
from app.rag.preprocessors.query_enhancer import get_query_enhancer
from app.rag.vector_db.reranker import get_category_reranker, RerankedResult
from app.core.logger import get_logger, rag_logger

logger = get_logger(__name__)


DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.65


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
        logger.debug(f"[RuleVectorDB.__new__] 创建实例: collection_name={collection_name}")
        if collection_name not in cls._instances:
            instance = super(RuleVectorDB, cls).__new__(cls)
            cls._instances[collection_name] = instance
            logger.debug(f"[RuleVectorDB] 新实例已创建: {collection_name}")
        return cls._instances[collection_name]
    
    def __init__(self, collection_name: str = "zongce_rules"):
        """
        初始化规则向量数据库
        
        Args:
            collection_name: 集合名称
        """
        if hasattr(self, '_initialized') and self._initialized:
            logger.debug(f"[RuleVectorDB] 已初始化，跳过: {collection_name}")
            return
        
        start_time = time.time()
        logger.info(f"[RuleVectorDB.__init__] 开始初始化: {collection_name}")
        
        try:
            super().__init__(collection_name)
        except Exception as e:
            logger.warning(f"[RuleVectorDB] 父类初始化失败: {e}")
            self.collection = None
            self.client = None
            self.embedding_func = None
        
        self.logger = get_logger(__name__)
        
        try:
            self.intent_recognizer = get_intent_recognizer()
        except Exception as e:
            logger.warning(f"[RuleVectorDB] 意图识别器初始化失败: {e}")
            self.intent_recognizer = None
        
        try:
            self.query_enhancer = get_query_enhancer()
        except Exception as e:
            logger.warning(f"[RuleVectorDB] 查询增强器初始化失败: {e}")
            self.query_enhancer = None
        
        try:
            self.reranker = get_category_reranker()
        except Exception as e:
            logger.warning(f"[RuleVectorDB] 重排序器初始化失败: {e}")
            self.reranker = None
        
        self._initialized = True
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[RuleVectorDB] 初始化完成: {collection_name}",
            extra={
                'duration_ms': duration_ms,
                'params': {'collection_name': collection_name}
            }
        )
    
    def add_documents(self, documents: List[Any]):
        """
        添加文档到向量库
        
        Args:
            documents: 文档列表，支持LangChain Document或自定义字典格式
        """
        start_time = time.time()
        logger.info(f"[add_documents] 开始添加文档: count={len(documents) if documents else 0}")
        
        if not documents:
            self.logger.warning("[add_documents] 没有文档需要添加到向量库")
            return
        
        try:
            existing_count = self.collection.count()
            logger.debug(f"[add_documents] 现有文档数: {existing_count}")
            
            texts, metadatas = self._prepare_documents_for_add(documents)
            ids = self._generate_document_ids(len(documents), existing_count)
            
            logger.debug(f"[add_documents] 准备添加: texts={len(texts)}, ids={len(ids)}")
            
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[add_documents] 添加完成: {len(documents)}个文档",
                extra={
                    'duration_ms': duration_ms,
                    'params': {
                        'document_count': len(documents),
                        'existing_count': existing_count,
                        'new_count': existing_count + len(documents)
                    }
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[add_documents] 添加失败: {e}",
                extra={'duration_ms': duration_ms},
                exc_info=True
            )
            raise
    
    def _build_query_params(
        self,
        query: str,
        top_k: int,
        metadata_filter: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        构建查询参数
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            metadata_filter: 元数据过滤条件
            
        Returns:
            查询参数字典
        """
        params = {
            "query_texts": [query],
            "n_results": top_k
        }
        
        if metadata_filter:
            params["where"] = metadata_filter
        
        return params
    
    def _process_query_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理查询结果
        
        Args:
            results: 原始查询结果
            
        Returns:
            处理后的结果
        """
        if not results:
            return {
                "documents": [],
                "metadatas": [],
                "distances": []
            }
        
        documents = results.get("documents", [[]])
        metadatas = results.get("metadatas", [[]])
        distances = results.get("distances", [[]])
        
        if documents and isinstance(documents[0], list):
            documents = documents[0]
        if metadatas and isinstance(metadatas[0], list):
            metadatas = metadatas[0]
        if distances and isinstance(distances[0], list):
            distances = distances[0]
        
        return {
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances
        }
    
    def search_relevant(
        self,
        query: str,
        top_k: int = None,
        metadata_filter: Optional[Dict] = None,
        similarity_threshold: float = None
    ):
        """
        检索相关规则
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量（默认5）
            metadata_filter: 元数据过滤条件，例如 {"type": "competition"} 或 {"category": "A类"}
            similarity_threshold: 相似度阈值（默认0.7），低于此阈值的结果将被过滤
            
        Returns:
            检索结果，包含文档、元数据和距离
        """
        start_time = time.time()
        
        if top_k is None:
            top_k = DEFAULT_TOP_K
        
        if similarity_threshold is None:
            similarity_threshold = DEFAULT_SIMILARITY_THRESHOLD
        
        logger.info(
            f"[search_relevant] 开始检索: query='{query[:50]}{'...' if len(query) > 50 else ''}', "
            f"top_k={top_k}, threshold={similarity_threshold}"
        )
        logger.debug(f"[search_relevant] 元数据过滤器: {metadata_filter}")
        
        try:
            query_params = self._build_query_params(query, top_k * 2, metadata_filter)
            logger.debug(f"[search_relevant] 查询参数构建完成")
            
            results = self.collection.query(**query_params)
            
            processed_results = self._process_query_results(results)
            
            filtered_results = self._filter_by_similarity(
                processed_results,
                similarity_threshold
            )
            
            final_results = self._limit_results(filtered_results, top_k)
            
            result_count = len(final_results.get('documents', []))
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"[search_relevant] 检索完成: 返回{result_count}条结果（阈值过滤后）",
                extra={
                    'duration_ms': duration_ms,
                    'params': {
                        'query_length': len(query),
                        'top_k': top_k,
                        'similarity_threshold': similarity_threshold,
                        'result_count': result_count,
                        'has_filter': metadata_filter is not None
                    }
                }
            )
            
            rag_logger.log_retrieval(query, metadata_filter or {}, result_count, duration_ms)
            
            return final_results
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[search_relevant] 检索失败: {e}",
                extra={'duration_ms': duration_ms},
                exc_info=True
            )
            return {
                "documents": [],
                "metadatas": [],
                "distances": []
            }
    
    def _filter_by_similarity(
        self,
        results: Dict[str, Any],
        threshold: float
    ) -> Dict[str, Any]:
        """根据相似度阈值过滤结果
        
        Args:
            results: 检索结果
            threshold: 相似度阈值（0-1）
            
        Returns:
            过滤后的结果
        """
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        distances = results.get("distances", [])
        
        if not documents:
            return results
        
        filtered_docs = []
        filtered_metas = []
        filtered_dists = []
        
        for doc, meta, dist in zip(documents, metadatas, distances):
            similarity = 1 / (1 + dist)
            
            if similarity >= threshold:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
                filtered_dists.append(dist)
            else:
                logger.debug(f"[_filter_by_similarity] 过滤低相似度结果: similarity={similarity:.3f}")
        
        logger.debug(
            f"[_filter_by_similarity] 过滤完成: {len(documents)} -> {len(filtered_docs)}条"
        )
        
        return {
            "documents": filtered_docs,
            "metadatas": filtered_metas,
            "distances": filtered_dists
        }
    
    def _limit_results(
        self,
        results: Dict[str, Any],
        top_k: int
    ) -> Dict[str, Any]:
        """限制结果数量
        
        Args:
            results: 检索结果
            top_k: 最大返回数量
            
        Returns:
            限制后的结果
        """
        return {
            "documents": results.get("documents", [])[:top_k],
            "metadatas": results.get("metadatas", [])[:top_k],
            "distances": results.get("distances", [])[:top_k]
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
        logger.info(f"[search_competition_category] 搜索竞赛类别: {competition_name}")
        
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
        logger.info(f"[search_category_score] 搜索类别分数: {category}")
        
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
        start_time = time.time()
        logger.info("[clear_all_documents] 开始清空文档")
        
        try:
            count = self.collection.count()
            logger.debug(f"[clear_all_documents] 当前文档数: {count}")
            
            if count > 0:
                all_data = self.collection.get()
                if all_data and 'ids' in all_data and all_data['ids']:
                    self.collection.delete(ids=all_data['ids'])
                    duration_ms = int((time.time() - start_time) * 1000)
                    logger.info(
                        f"[clear_all_documents] 清空完成: 删除{len(all_data['ids'])}个文档",
                        extra={'duration_ms': duration_ms, 'params': {'deleted_count': len(all_data['ids'])}}
                    )
                else:
                    logger.warning("[clear_all_documents] 集合为空，无需删除")
            else:
                logger.warning("[clear_all_documents] 集合为空，无需删除")
        except Exception as e:
            logger.error(f"[clear_all_documents] 清空失败: {e}", exc_info=True)
            try:
                self.client.delete_collection(name=self.collection_name)
                self.collection = self._get_or_create_collection(self.client)
                logger.info("[clear_all_documents] 已重新创建集合")
            except Exception as e2:
                logger.error(f"[clear_all_documents] 重新创建集合失败: {e2}", exc_info=True)
                raise
    
    def update_document_metadata(self, doc_id: str, metadata: Dict[str, Any]):
        """
        更新文档元数据
        
        Args:
            doc_id: 文档ID
            metadata: 新的元数据
        """
        logger.info(f"[update_document_metadata] 更新文档元数据: doc_id={doc_id}")
        
        try:
            result = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
            
            if result and 'documents' in result and result['documents']:
                self.collection.delete(ids=[doc_id])
                
                self.collection.add(
                    ids=[doc_id],
                    documents=[result['documents'][0]],
                    metadatas=[metadata]
                )
                logger.info(f"[update_document_metadata] 更新成功: doc_id={doc_id}")
            else:
                logger.warning(f"[update_document_metadata] 未找到文档: doc_id={doc_id}")
        except Exception as e:
            logger.error(f"[update_document_metadata] 更新失败: {e}", exc_info=True)
            raise
    
    def delete_documents_by_filter(self, metadata_filter: Dict[str, Any]):
        """
        根据元数据过滤条件删除文档
        
        Args:
            metadata_filter: 元数据过滤条件
        """
        logger.info(f"[delete_documents_by_filter] 按条件删除文档: filter={metadata_filter}")
        
        try:
            filtered_docs = self.collection.get(where=metadata_filter)
            
            if filtered_docs and 'ids' in filtered_docs and filtered_docs['ids']:
                self.collection.delete(ids=filtered_docs['ids'])
                logger.info(f"[delete_documents_by_filter] 删除完成: {len(filtered_docs['ids'])}个文档")
            else:
                logger.warning("[delete_documents_by_filter] 没有找到符合条件的文档")
        except Exception as e:
            logger.error(f"[delete_documents_by_filter] 删除失败: {e}", exc_info=True)
            raise
    
    def get_document_by_id(self, doc_id: str):
        """
        根据ID获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档内容
        """
        logger.debug(f"[get_document_by_id] 获取文档: doc_id={doc_id}")
        
        try:
            result = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
            
            if result and 'documents' in result and result['documents']:
                logger.debug(f"[get_document_by_id] 获取成功: doc_id={doc_id}")
                return {
                    "id": doc_id,
                    "content": result['documents'][0],
                    "metadata": result['metadatas'][0] if result['metadatas'] else {}
                }
            else:
                logger.warning(f"[get_document_by_id] 未找到文档: doc_id={doc_id}")
                return None
        except Exception as e:
            logger.error(f"[get_document_by_id] 获取失败: {e}", exc_info=True)
            raise
    
    def search_with_category_awareness(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        use_rerank: bool = True,
        intent: IntentResult = None,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> Tuple[List[RerankedResult], IntentResult]:
        """
        类别感知检索（核心方法）
        
        自动识别意图、增强查询、执行检索、重排结果
        
        Args:
            query: 用户查询
            top_k: 返回结果数量（默认5）
            use_rerank: 是否使用重排
            intent: 预先识别的意图（可选）
            similarity_threshold: 相似度阈值（默认0.7）
            
        Returns:
            (重排结果列表, 意图识别结果)
        """
        start_time = time.time()
        logger.info(f"[search_with_category_awareness] 开始类别感知检索: '{query[:50]}'")
        
        if intent is None:
            logger.debug("[search_with_category_awareness] 自动识别意图")
            intent = self.intent_recognizer.recognize(query)
        
        if intent.requires_manual_review:
            logger.info(f"[search_with_category_awareness] 查询需人工审核: {query}")
            rag_logger.log_error("search_with_category_awareness", 
                                Exception("需要人工审核"), 
                                {"query": query, "intent": intent.to_dict()})
            return [], intent
        
        enhanced_query = self.query_enhancer.enhance(query, intent)
        metadata_filter = self.query_enhancer.build_metadata_filter(intent)
        
        logger.info(f"[search_with_category_awareness] 增强查询: '{enhanced_query[:60]}'")
        logger.debug(f"[search_with_category_awareness] 元数据过滤器: {metadata_filter}")
        
        results = self.search_relevant(
            query=enhanced_query,
            top_k=top_k * 2,
            metadata_filter=metadata_filter,
            similarity_threshold=similarity_threshold
        )
        
        if use_rerank:
            logger.debug("[search_with_category_awareness] 执行重排")
            reranked = self.reranker.rerank(results, query, intent, top_k)
        else:
            logger.debug("[search_with_category_awareness] 跳过重排")
            reranked = self._convert_to_reranked(results, top_k)
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[search_with_category_awareness] 检索完成: 返回{len(reranked)}条结果",
            extra={
                'duration_ms': duration_ms,
                'params': {
                    'query': query[:50] if len(query) > 50 else query,
                    'sub_category': intent.sub_category,
                    'competition_type': intent.competition_type,
                    'result_count': len(reranked),
                    'use_rerank': use_rerank,
                    'similarity_threshold': similarity_threshold
                }
            }
        )
        
        rag_logger.log_performance("category_aware_search", duration_ms, {
            "result_count": len(reranked),
            "intent": intent.to_dict()
        })
        
        return reranked, intent
    
    def _convert_to_reranked(
        self,
        results: Dict[str, Any],
        top_k: int
    ) -> List[RerankedResult]:
        """将普通结果转换为RerankedResult格式
        
        Args:
            results: 检索结果
            top_k: 返回数量
            
        Returns:
            RerankedResult列表
        """
        logger.debug(f"[_convert_to_reranked] 转换结果: top_k={top_k}")
        reranked = []
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [{}] * len(documents))
        distances = results.get("distances", [0.5] * len(documents))
        
        if isinstance(documents[0], list) if documents else False:
            documents = documents[0]
            metadatas = metadatas[0] if metadatas else []
            distances = distances[0] if distances else []
        
        for i, (doc, meta, dist) in enumerate(zip(documents[:top_k], metadatas[:top_k], distances[:top_k])):
            reranked.append(RerankedResult(
                document=doc,
                metadata=meta,
                original_distance=dist,
                reranked_score=1 / (1 + dist),
                score_breakdown={"similarity": 1 / (1 + dist)}
            ))
        
        return reranked
    
    def search_competition_score(
        self,
        competition_name: str,
        award_level: str = "一等奖",
        top_k: int = 5
    ) -> Tuple[List[RerankedResult], Dict[str, Any]]:
        """
        搜索竞赛加分
        
        Args:
            competition_name: 竞赛名称
            award_level: 获奖等级
            top_k: 返回结果数量
            
        Returns:
            (重排结果列表, 竞赛信息)
        """
        start_time = time.time()
        logger.info(f"[search_competition_score] 搜索竞赛加分: '{competition_name}', {award_level}")
        
        from app.rag.preprocessors.competition_mapper import get_competition_mapper
        
        mapper = get_competition_mapper()
        std_name, comp_info, match_score = mapper.normalize_name(competition_name)
        
        competition_info = {
            "original_name": competition_name,
            "standard_name": std_name,
            "match_score": match_score,
            "competition_type": comp_info.competition_type if comp_info else None,
            "level": comp_info.level if comp_info else None,
            "requires_manual_review": comp_info.requires_manual_review if comp_info else False
        }
        
        logger.debug(f"[search_competition_score] 竞赛信息: {competition_info}")
        
        if comp_info and comp_info.requires_manual_review:
            logger.info(f"[search_competition_score] 非AB类竞赛，需人工审核: {std_name}")
            return [], competition_info
        
        query = f"{std_name or competition_name} {award_level} 加分"
        
        intent = IntentResult(
            main_category="C",
            sub_category="C1",
            competition_type=comp_info.competition_type if comp_info else None,
            level=comp_info.level if comp_info else None,
            award_level=award_level,
            competition_name=std_name,
            confidence=match_score / 100.0 if match_score else 0.5
        )
        
        results, _ = self.search_with_category_awareness(query, top_k, intent=intent)
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[search_competition_score] 搜索完成: {len(results)}条结果",
            extra={'duration_ms': duration_ms}
        )
        
        return results, competition_info
    
    def search_certificate_score(
        self,
        certificate_name: str,
        top_k: int = 3
    ) -> Tuple[List[RerankedResult], Dict[str, Any]]:
        """
        搜索证书加分
        
        Args:
            certificate_name: 证书名称
            top_k: 返回结果数量
            
        Returns:
            (重排结果列表, 证书信息)
        """
        start_time = time.time()
        logger.info(f"[search_certificate_score] 搜索证书加分: '{certificate_name}'")
        
        from app.rag.utils.category_keywords import CERTIFICATE_SCORES
        
        cert_info = None
        cert_type = None
        
        cert_patterns = {
            "CET4": ["四级", "cet4", "英语四级"],
            "CET6": ["六级", "cet6", "英语六级"],
            "NCRE2": ["计算机二级", "ncre2"],
            "NCRE3": ["计算机三级", "ncre3"],
            "NCRE4": ["计算机四级", "ncre4"],
            "NETWORK_ENGINEER": ["网络工程师"],
        }
        
        cert_name_lower = certificate_name.lower()
        for ct, patterns in cert_patterns.items():
            for pattern in patterns:
                if pattern in cert_name_lower:
                    cert_type = ct
                    cert_info = CERTIFICATE_SCORES.get(ct)
                    break
            if cert_type:
                break
        
        certificate_info = {
            "original_name": certificate_name,
            "certificate_type": cert_type,
            "standard_name": cert_info["name"] if cert_info else certificate_name,
            "default_score": cert_info["score"] if cert_info else None,
            "category": cert_info["category"] if cert_info else "C3"
        }
        
        logger.debug(f"[search_certificate_score] 证书信息: {certificate_info}")
        
        query = f"{cert_info['name'] if cert_info else certificate_name} 加分"
        
        intent = IntentResult(
            main_category="C",
            sub_category="C3",
            certificate_type=cert_type,
            confidence=0.9 if cert_info else 0.5
        )
        
        results, _ = self.search_with_category_awareness(query, top_k, intent=intent)
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[search_certificate_score] 搜索完成: {len(results)}条结果",
            extra={'duration_ms': duration_ms}
        )
        
        return results, certificate_info
    
    def search_by_sub_category(
        self,
        query: str,
        sub_category: str,
        top_k: int = 5
    ) -> List[RerankedResult]:
        """
        按子类别检索
        
        Args:
            query: 查询文本
            sub_category: 子类别（C1/C2/C3/C4）
            top_k: 返回结果数量
            
        Returns:
            重排结果列表
        """
        logger.info(f"[search_by_sub_category] 按子类别检索: sub_category={sub_category}")
        
        intent = IntentResult(
            main_category="C",
            sub_category=sub_category,
            confidence=0.7
        )
        
        results, _ = self.search_with_category_awareness(query, top_k, intent=intent)
        return results
    
    def get_category_stats(self) -> Dict[str, Any]:
        """
        获取类别统计信息
        
        Returns:
            类别统计字典
        """
        logger.debug("[get_category_stats] 获取类别统计")
        
        try:
            all_data = self.collection.get(include=["metadatas"])
            
            stats = {
                "total": len(all_data["ids"]) if all_data else 0,
                "by_type": {},
                "by_main_category": {},
                "by_sub_category": {},
                "by_competition_type": {},
                "by_level": {},
                "manual_review_count": 0
            }
            
            if all_data and all_data.get("metadatas"):
                for meta in all_data["metadatas"]:
                    doc_type = meta.get("type", "unknown")
                    stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
                    
                    main_cat = meta.get("main_category", "unknown")
                    stats["by_main_category"][main_cat] = stats["by_main_category"].get(main_cat, 0) + 1
                    
                    sub_cat = meta.get("sub_category", "unknown")
                    stats["by_sub_category"][sub_cat] = stats["by_sub_category"].get(sub_cat, 0) + 1
                    
                    comp_type = meta.get("competition_type")
                    if comp_type:
                        stats["by_competition_type"][comp_type] = stats["by_competition_type"].get(comp_type, 0) + 1
                    
                    level = meta.get("level")
                    if level:
                        stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
                    
                    if meta.get("requires_manual_review"):
                        stats["manual_review_count"] += 1
            
            logger.info(
                f"[get_category_stats] 统计完成: 总计{stats['total']}条",
                extra={'params': stats}
            )
            return stats
            
        except Exception as e:
            logger.error(f"[get_category_stats] 获取统计失败: {e}", exc_info=True)
            return {"error": str(e)}


def get_vector_db(collection_name: str = "zongce_rules") -> RuleVectorDB:
    """
    获取向量数据库单例实例的便捷函数
    
    Args:
        collection_name: 集合名称，默认为"zongce_rules"
        
    Returns:
        RuleVectorDB单例实例
    """
    logger.debug(f"[get_vector_db] 获取向量数据库实例: {collection_name}")
    return RuleVectorDB(collection_name)
