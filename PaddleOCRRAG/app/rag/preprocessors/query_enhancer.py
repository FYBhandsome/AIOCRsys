"""
查询增强器
负责构建带类别标签的增强查询
"""
import time
from typing import Dict, Optional, Any

from app.rag.preprocessors.intent_recognizer import IntentResult, get_intent_recognizer
from app.core.logger import get_logger, rag_logger

logger = get_logger(__name__)


class QueryEnhancer:
    """查询增强器"""
    
    def __init__(self):
        logger.debug("[QueryEnhancer.__init__] 初始化查询增强器")
        self.logger = get_logger(__name__)
        self.intent_recognizer = get_intent_recognizer()
        logger.debug("[QueryEnhancer] 初始化完成")
    
    def enhance(self, query: str, intent: IntentResult = None) -> str:
        """增强查询，添加类别标签
        
        Args:
            query: 原始查询
            intent: 意图识别结果（可选，不提供则自动识别）
            
        Returns:
            增强后的查询
        """
        start_time = time.time()
        logger.debug(f"[enhance] 开始增强查询: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        if intent is None:
            logger.debug("[enhance] 未提供intent，自动识别")
            intent = self.intent_recognizer.recognize(query)
        
        if intent.requires_manual_review:
            enhanced = f"【人工审核】{query}"
            logger.info(f"[enhance] 查询需人工审核: '{query[:30]}'")
            return enhanced
        
        tags = self._build_tags(intent)
        
        if tags:
            enhanced = f"【{tags}】{query}"
        else:
            enhanced = query
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[enhance] 查询增强完成: '{enhanced[:60]}{'...' if len(enhanced) > 60 else ''}'",
            extra={
                'duration_ms': duration_ms,
                'params': {
                    'original_length': len(query),
                    'enhanced_length': len(enhanced),
                    'tags': tags
                }
            }
        )
        
        return enhanced
    
    def _build_tags(self, intent: IntentResult) -> str:
        """构建标签字符串
        
        Args:
            intent: 意图识别结果
            
        Returns:
            标签字符串
        """
        logger.debug(f"[_build_tags] 构建标签: sub_cat={intent.sub_category}, type={intent.competition_type}")
        tags = []
        
        if intent.main_category:
            tags.append(f"主类:{intent.main_category}")
        
        if intent.sub_category:
            tags.append(f"子类:{intent.sub_category}")
        
        if intent.competition_type:
            tags.append(f"竞赛类型:{intent.competition_type}")
        
        if intent.level:
            tags.append(f"级别:{intent.level}")
        
        if intent.award_level:
            tags.append(f"获奖等级:{intent.award_level}")
        
        if intent.certificate_type:
            tags.append(f"证书:{intent.certificate_type}")
        
        result = "｜".join(tags)
        logger.debug(f"[_build_tags] 标签结果: {result}")
        return result
    
    def build_metadata_filter(self, intent: IntentResult) -> Dict[str, Any]:
        """构建元数据过滤器
        
        Args:
            intent: 意图识别结果
            
        Returns:
            元数据过滤条件
        """
        logger.debug(f"[build_metadata_filter] 构建过滤器: sub_cat={intent.sub_category}")
        filters = []
        
        if intent.main_category:
            filters.append({"main_category": intent.main_category})
        
        if intent.sub_category:
            filters.append({"sub_category": intent.sub_category})
        
        if intent.competition_type and intent.competition_type != "非AB":
            filters.append({"competition_type": intent.competition_type})
        
        if intent.level:
            filters.append({"level": intent.level})
        
        if intent.certificate_type:
            filters.append({"certificate_type": intent.certificate_type})
        
        if len(filters) == 0:
            logger.debug("[build_metadata_filter] 无过滤条件")
            return None
        elif len(filters) == 1:
            result = filters[0]
            logger.debug(f"[build_metadata_filter] 单条件过滤: {result}")
            return result
        else:
            result = {"$and": filters}
            logger.debug(f"[build_metadata_filter] 复合条件过滤: {len(filters)}个条件")
            return result
    
    def enhance_with_context(
        self, 
        query: str, 
        main_category: str = None,
        sub_category: str = None,
        competition_type: str = None,
        level: str = None,
        award_level: str = None
    ) -> str:
        """手动指定上下文增强查询
        
        Args:
            query: 原始查询
            main_category: 主类别
            sub_category: 子类别
            competition_type: 竞赛类型
            level: 级别
            award_level: 获奖等级
            
        Returns:
            增强后的查询
        """
        logger.info(
            f"[enhance_with_context] 手动增强: sub_cat={sub_category}, type={competition_type}, level={level}"
        )
        intent = IntentResult(
            main_category=main_category or "C",
            sub_category=sub_category,
            competition_type=competition_type,
            level=level,
            award_level=award_level
        )
        return self.enhance(query, intent)
    
    def get_search_context(self, query: str) -> Dict[str, Any]:
        """获取完整的搜索上下文
        
        Args:
            query: 原始查询
            
        Returns:
            包含增强查询、元数据过滤器等的字典
        """
        start_time = time.time()
        logger.info(f"[get_search_context] 获取搜索上下文: '{query[:50]}'")
        
        intent = self.intent_recognizer.recognize(query)
        
        context = {
            "original_query": query,
            "enhanced_query": self.enhance(query, intent),
            "metadata_filter": self.build_metadata_filter(intent),
            "intent": intent.to_dict(),
            "requires_manual_review": intent.requires_manual_review
        }
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[get_search_context] 上下文构建完成",
            extra={
                'duration_ms': duration_ms,
                'params': {
                    'requires_manual_review': intent.requires_manual_review,
                    'has_filter': context['metadata_filter'] is not None
                }
            }
        )
        
        return context


query_enhancer = QueryEnhancer()


def get_query_enhancer() -> QueryEnhancer:
    """获取查询增强器实例
    
    Returns:
        QueryEnhancer实例
    """
    logger.debug("[get_query_enhancer] 获取查询增强器实例")
    return query_enhancer
