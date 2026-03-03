"""
意图识别器
负责分析用户查询，预测主/子类别、竞赛类型、级别等
"""
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from app.rag.utils.category_keywords import (
    CATEGORY_KEYWORDS,
    COMPETITION_TYPE_KEYWORDS,
    LEVEL_KEYWORDS,
    AWARD_LEVEL_KEYWORDS,
    CERTIFICATE_SCORES
)
from app.rag.preprocessors.competition_mapper import get_competition_mapper
from app.core.logger import get_logger, rag_logger

logger = get_logger(__name__)


@dataclass
class IntentResult:
    """意图识别结果"""
    main_category: str = "C"
    sub_category: Optional[str] = None
    competition_type: Optional[str] = None
    level: Optional[str] = None
    award_level: Optional[str] = None
    certificate_type: Optional[str] = None
    competition_name: Optional[str] = None
    confidence: float = 0.0
    requires_manual_review: bool = False
    matched_keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "main_category": self.main_category,
            "sub_category": self.sub_category,
            "competition_type": self.competition_type,
            "level": self.level,
            "award_level": self.award_level,
            "certificate_type": self.certificate_type,
            "competition_name": self.competition_name,
            "confidence": self.confidence,
            "requires_manual_review": self.requires_manual_review,
            "matched_keywords": self.matched_keywords
        }


class IntentRecognizer:
    """意图识别器"""
    
    def __init__(self):
        logger.debug("[IntentRecognizer.__init__] 初始化意图识别器")
        self.logger = get_logger(__name__)
        self.competition_mapper = None
    
    def _get_competition_mapper(self):
        """延迟加载竞赛映射器"""
        if self.competition_mapper is None:
            logger.debug("[_get_competition_mapper] 延迟加载竞赛映射器")
            try:
                self.competition_mapper = get_competition_mapper()
                logger.debug("[_get_competition_mapper] 竞赛映射器加载成功")
            except Exception as e:
                logger.warning(f"[_get_competition_mapper] 加载竞赛映射器失败: {e}")
        return self.competition_mapper
    
    def recognize(self, query: str) -> IntentResult:
        """识别用户查询意图
        
        Args:
            query: 用户查询文本
            
        Returns:
            IntentResult意图识别结果
        """
        start_time = time.time()
        logger.info(f"[recognize] 开始识别意图: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        result = IntentResult()
        query_lower = query.lower()
        
        competition_name, comp_info, match_score = self._extract_competition(query)
        if comp_info:
            result.competition_name = competition_name
            result.competition_type = comp_info.competition_type
            result.level = comp_info.level
            result.requires_manual_review = comp_info.requires_manual_review
            result.confidence = match_score / 100.0
            result.sub_category = "C1"
            result.matched_keywords.append(competition_name)
            logger.debug(f"[recognize] 竞赛匹配成功: '{competition_name}', 类型={comp_info.competition_type}")
        
        if result.sub_category is None:
            sub_cat, matched_kw = self._predict_sub_category(query)
            result.sub_category = sub_cat
            result.matched_keywords.extend(matched_kw)
            logger.debug(f"[recognize] 子类别预测: {sub_cat}, 关键词: {matched_kw}")
        
        if result.level is None:
            level, matched_kw = self._extract_level(query)
            result.level = level
            result.matched_keywords.extend(matched_kw)
        
        if result.award_level is None:
            award_level, matched_kw = self._extract_award_level(query)
            result.award_level = award_level
            result.matched_keywords.extend(matched_kw)
        
        cert_type, cert_info = self._extract_certificate(query)
        if cert_type:
            result.certificate_type = cert_type
            result.sub_category = "C3"
            result.matched_keywords.append(cert_info["name"])
            logger.debug(f"[recognize] 证书识别: {cert_type}")
        
        result.matched_keywords = list(set(result.matched_keywords))
        
        if result.confidence == 0 and result.sub_category:
            result.confidence = 0.5 + len(result.matched_keywords) * 0.1
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"[recognize] 意图识别完成: 子类={result.sub_category}, 类型={result.competition_type}, 置信度={result.confidence:.2f}",
            extra={
                'duration_ms': duration_ms,
                'params': {
                    'query': query[:50] if len(query) > 50 else query,
                    'sub_category': result.sub_category,
                    'competition_type': result.competition_type,
                    'confidence': result.confidence
                }
            }
        )
        
        rag_logger.log_query(query, result.to_dict())
        rag_logger.log_performance("intent_recognition", duration_ms, result.to_dict())
        
        return result
    
    def _extract_competition(self, query: str) -> Tuple[Optional[str], Optional[Any], int]:
        """提取竞赛名称
        
        Args:
            query: 用户查询
            
        Returns:
            (标准竞赛名称, 竞赛信息, 匹配分数)
        """
        logger.debug(f"[_extract_competition] 提取竞赛: '{query[:30]}'")
        mapper = self._get_competition_mapper()
        if mapper is None:
            logger.warning("[_extract_competition] 竞赛映射器不可用")
            return None, None, 0
        
        patterns = [
            r'[《"]([^》"]+)[》"]',
            r'["""]([^"""]+)["""]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                name = match.group(1)
                std_name, info, score = mapper.normalize_name(name)
                if info:
                    logger.debug(f"[_extract_competition] 引号内匹配: '{name}' -> '{std_name}'")
                    return std_name, info, score
        
        return mapper.normalize_name(query)
    
    def _predict_sub_category(self, query: str) -> Tuple[Optional[str], List[str]]:
        """预测子类别
        
        Args:
            query: 用户查询
            
        Returns:
            (子类别, 匹配的关键词列表)
        """
        logger.debug(f"[_predict_sub_category] 预测子类别")
        query_lower = query.lower()
        
        formula_keywords = ["综合测评", "计算公式", "占比", "M=", "品德行为分", "学习成绩分", "素质拓展分"]
        for kw in formula_keywords:
            if kw.lower() in query_lower:
                logger.debug(f"[_predict_sub_category] 检测到综合测评公式关键词: '{kw}', 跳过sub_category过滤")
                return None, [kw]
        
        scores = {}
        matched_keywords = {}
        
        for cat, info in CATEGORY_KEYWORDS.items():
            score = 0
            matched = []
            for keyword in info["keywords"]:
                if keyword.lower() in query_lower:
                    score += 1
                    matched.append(keyword)
            scores[cat] = score
            matched_keywords[cat] = matched
        
        if max(scores.values()) > 0:
            best_cat = max(scores, key=scores.get)
            logger.debug(f"[_predict_sub_category] 最佳匹配: {best_cat} (分数: {scores[best_cat]})")
            return best_cat, matched_keywords[best_cat]
        
        logger.debug("[_predict_sub_category] 无匹配, 默认C1")
        return "C1", []
    
    def _extract_level(self, query: str) -> Tuple[Optional[str], List[str]]:
        """提取竞赛级别
        
        Args:
            query: 用户查询
            
        Returns:
            (级别, 匹配的关键词列表)
        """
        logger.debug(f"[_extract_level] 提取级别")
        query_lower = query.lower()
        
        for level, keywords in LEVEL_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    logger.debug(f"[_extract_level] 匹配级别: {level}")
                    return level, [kw]
        
        return None, []
    
    def _extract_award_level(self, query: str) -> Tuple[Optional[str], List[str]]:
        """提取获奖等级
        
        Args:
            query: 用户查询
            
        Returns:
            (获奖等级, 匹配的关键词列表)
        """
        logger.debug(f"[_extract_award_level] 提取获奖等级")
        query_lower = query.lower()
        
        for award_level, keywords in AWARD_LEVEL_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    logger.debug(f"[_extract_award_level] 匹配获奖等级: {award_level}")
                    return award_level, [kw]
        
        return None, []
    
    def _extract_certificate(self, query: str) -> Tuple[Optional[str], Optional[Dict]]:
        """提取证书类型
        
        Args:
            query: 用户查询
            
        Returns:
            (证书类型, 证书信息)
        """
        logger.debug(f"[_extract_certificate] 提取证书")
        query_lower = query.lower()
        
        cert_patterns = {
            "CET4": [r'四级', r'cet[-_]?4', r'英语四级'],
            "CET6": [r'六级', r'cet[-_]?6', r'英语六级'],
            "NCRE2": [r'计算机二级', r'ncre[-_]?2'],
            "NCRE3": [r'计算机三级', r'ncre[-_]?3'],
            "NCRE4": [r'计算机四级', r'ncre[-_]?4'],
            "NETWORK_ENGINEER": [r'网络工程师'],
        }
        
        for cert_type, patterns in cert_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    logger.debug(f"[_extract_certificate] 匹配证书: {cert_type}")
                    return cert_type, CERTIFICATE_SCORES.get(cert_type)
        
        return None, None
    
    def get_category_description(self, sub_category: str) -> str:
        """获取类别描述
        
        Args:
            sub_category: 子类别
            
        Returns:
            类别描述
        """
        if sub_category in CATEGORY_KEYWORDS:
            return CATEGORY_KEYWORDS[sub_category]["name"]
        return "未知类别"


intent_recognizer = IntentRecognizer()


def get_intent_recognizer() -> IntentRecognizer:
    """获取意图识别器实例
    
    Returns:
        IntentRecognizer实例
    """
    logger.debug("[get_intent_recognizer] 获取意图识别器实例")
    return intent_recognizer
