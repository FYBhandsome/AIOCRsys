"""
类别感知重排器
对检索结果进行二次排序，提升类别匹配度
"""
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from app.rag.utils.category_keywords import CATEGORY_KEYWORDS
from app.rag.preprocessors.intent_recognizer import IntentResult
from app.core.logger import get_logger, rag_logger

logger = get_logger(__name__)


@dataclass
class RerankedResult:
    """重排结果"""
    document: str
    metadata: Dict[str, Any]
    original_distance: float
    reranked_score: float
    score_breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document,
            "metadata": self.metadata,
            "original_distance": self.original_distance,
            "reranked_score": self.reranked_score,
            "score_breakdown": self.score_breakdown
        }


class CategoryReranker:
    """类别感知重排器"""
    
    SCORE_WEIGHTS = {
        "similarity": 0.4,
        "category_match": 0.3,
        "keyword_match": 0.2,
        "source_authority": 0.1
    }
    
    CATEGORY_BONUS = {
        "main_match": 0.15,
        "sub_match": 0.15,
        "type_match": 0.10,
        "level_match": 0.10
    }
    
    SOURCE_AUTHORITY = {
        "细则": 1.0,
        "学科竞赛名称列表": 0.9,
        "其他": 0.7
    }
    
    def __init__(self):
        logger.debug("[CategoryReranker.__init__] 初始化类别感知重排器")
        self.logger = get_logger(__name__)
    
    def rerank(
        self,
        results: Dict[str, Any],
        query: str,
        intent: IntentResult = None,
        top_k: int = 5
    ) -> List[RerankedResult]:
        """重排检索结果
        
        Args:
            results: 检索结果，包含documents, metadatas, distances
            query: 原始查询
            intent: 意图识别结果
            top_k: 返回结果数量
            
        Returns:
            重排后的结果列表
        """
        start_time = time.time()
        logger.info(f"[rerank] 开始重排: query='{query[:30]}...', top_k={top_k}")
        
        if not results or not results.get("documents"):
            logger.warning("[rerank] 无检索结果，返回空列表")
            return []
        
        documents = results["documents"]
        metadatas = results.get("metadatas", [{}] * len(documents))
        distances = results.get("distances", [0.5] * len(documents))
        
        if isinstance(documents[0], list):
            documents = documents[0]
            metadatas = metadatas[0] if metadatas else [{}] * len(documents)
            distances = distances[0] if distances else [0.5] * len(documents)
        
        input_count = len(documents)
        logger.debug(f"[rerank] 输入文档数: {input_count}")
        
        reranked = []
        
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            score_breakdown = self._calculate_scores(doc, meta, dist, query, intent)
            
            total_score = sum(score_breakdown.values())
            
            result = RerankedResult(
                document=doc,
                metadata=meta,
                original_distance=dist,
                reranked_score=total_score,
                score_breakdown=score_breakdown
            )
            reranked.append(result)
            
            if i < 3:
                logger.debug(
                    f"[rerank] 结果{i+1}: score={total_score:.3f}, "
                    f"sub_cat={meta.get('sub_category')}, type={meta.get('competition_type')}"
                )
        
        reranked.sort(key=lambda x: x.reranked_score, reverse=True)
        
        output_count = min(top_k, len(reranked))
        top_score = reranked[0].reranked_score if reranked else 0
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"[rerank] 重排完成: {input_count} -> {output_count}条, 最高分={top_score:.3f}",
            extra={
                'duration_ms': duration_ms,
                'input_count': input_count,
                'output_count': output_count,
                'top_score': top_score
            }
        )
        
        rag_logger.log_rerank(input_count, output_count, top_score, duration_ms)
        
        return reranked[:top_k]
    
    def _calculate_scores(
        self,
        document: str,
        metadata: Dict[str, Any],
        distance: float,
        query: str,
        intent: IntentResult = None
    ) -> Dict[str, float]:
        """计算各项得分
        
        Args:
            document: 文档内容
            metadata: 元数据
            distance: 向量距离
            query: 查询文本
            intent: 意图识别结果
            
        Returns:
            得分明细
        """
        scores = {}
        
        sim_score = 1 / (1 + distance)
        scores["similarity"] = sim_score * self.SCORE_WEIGHTS["similarity"]
        
        category_score = self._calculate_category_score(metadata, intent)
        scores["category_match"] = category_score * self.SCORE_WEIGHTS["category_match"]
        
        keyword_score = self._calculate_keyword_score(document, query, metadata)
        scores["keyword_match"] = keyword_score * self.SCORE_WEIGHTS["keyword_match"]
        
        source_score = self._calculate_source_score(metadata)
        scores["source_authority"] = source_score * self.SCORE_WEIGHTS["source_authority"]
        
        return scores
    
    def _calculate_category_score(
        self,
        metadata: Dict[str, Any],
        intent: IntentResult = None
    ) -> float:
        """计算类别匹配得分
        
        Args:
            metadata: 文档元数据
            intent: 意图识别结果
            
        Returns:
            类别匹配得分
        """
        if intent is None:
            return 0.5
        
        score = 0.0
        matches = []
        
        if intent.main_category and metadata.get("main_category") == intent.main_category:
            score += self.CATEGORY_BONUS["main_match"]
            matches.append("main")
        
        if intent.sub_category and metadata.get("sub_category") == intent.sub_category:
            score += self.CATEGORY_BONUS["sub_match"]
            matches.append("sub")
        
        if intent.competition_type and metadata.get("competition_type") == intent.competition_type:
            score += self.CATEGORY_BONUS["type_match"]
            matches.append("type")
        
        if intent.level and metadata.get("level") == intent.level:
            score += self.CATEGORY_BONUS["level_match"]
            matches.append("level")
        
        if matches:
            logger.debug(f"[_calculate_category_score] 匹配: {matches}, 得分: {score:.2f}")
        
        return min(1.0, score)
    
    def _calculate_keyword_score(
        self,
        document: str,
        query: str,
        metadata: Dict[str, Any]
    ) -> float:
        """计算关键词匹配得分
        
        Args:
            document: 文档内容
            query: 查询文本
            metadata: 元数据
            
        Returns:
            关键词匹配得分
        """
        score = 0.0
        
        sub_category = metadata.get("sub_category")
        if sub_category and sub_category in CATEGORY_KEYWORDS:
            keywords = CATEGORY_KEYWORDS[sub_category]["keywords"]
            matched = sum(1 for kw in keywords if kw in query or kw in document)
            score = min(1.0, matched * 0.1)
        
        doc_lower = document.lower()
        query_lower = query.lower()
        
        important_pairs = [
            ("一等奖", "一等奖"),
            ("二等奖", "二等奖"),
            ("三等奖", "三等奖"),
            ("国家级", "国家级"),
            ("省部级", "省部级"),
            ("A类", "A类"),
            ("B类", "B类"),
        ]
        
        for doc_kw, query_kw in important_pairs:
            if doc_kw in doc_lower and query_kw in query_lower:
                score += 0.1
        
        return min(1.0, score)
    
    def _calculate_source_score(self, metadata: Dict[str, Any]) -> float:
        """计算来源权威性得分
        
        Args:
            metadata: 元数据
            
        Returns:
            来源权威性得分
        """
        source = metadata.get("source", "")
        
        for key, score in self.SOURCE_AUTHORITY.items():
            if key in source:
                return score
        
        return self.SOURCE_AUTHORITY["其他"]
    
    def filter_manual_review(
        self,
        results: List[RerankedResult]
    ) -> Tuple[List[RerankedResult], List[RerankedResult]]:
        """分离需要人工审核的结果
        
        Args:
            results: 重排结果列表
            
        Returns:
            (正常结果, 需人工审核结果)
        """
        logger.debug(f"[filter_manual_review] 分离人工审核结果: {len(results)}条")
        normal = []
        manual_review = []
        
        for result in results:
            if result.metadata.get("requires_manual_review"):
                manual_review.append(result)
            else:
                normal.append(result)
        
        logger.info(
            f"[filter_manual_review] 分离完成: 正常{len(normal)}条, 人工审核{len(manual_review)}条"
        )
        return normal, manual_review
    
    def get_top_result(self, results: List[RerankedResult]) -> Optional[RerankedResult]:
        """获取最佳结果
        
        Args:
            results: 重排结果列表
            
        Returns:
            最佳结果
        """
        if not results:
            logger.debug("[get_top_result] 无结果")
            return None
        logger.debug(f"[get_top_result] 返回最佳结果: score={results[0].reranked_score:.3f}")
        return results[0]


category_reranker = CategoryReranker()


def get_category_reranker() -> CategoryReranker:
    """获取重排器实例
    
    Returns:
        CategoryReranker实例
    """
    logger.debug("[get_category_reranker] 获取重排器实例")
    return category_reranker
