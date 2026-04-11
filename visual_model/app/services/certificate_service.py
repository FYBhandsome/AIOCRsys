#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书分类和算分服务

根据证书内容判断证书类别（A类/C类）并计算分数
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.logger import logger
from app.services.rag_client import get_rag_client
from config import settings


class CertificateClassificationService:
    """证书分类和算分服务"""
    
    def __init__(self):
        """初始化服务"""
        self.rag_client = get_rag_client() if settings.RAG_ENABLED else None
        logger.info("证书分类服务初始化完成")
    
    async def classify_and_calculate_score(
        self,
        certificate_text: str,
        certificate_info: Optional[Dict[str, Any]] = None,
        student_info: Optional[Dict[str, Any]] = None,
        rag_rules: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """分类证书并计算分数
        
        Args:
            certificate_text: 证书文本内容
            certificate_info: 证书详细信息（可选）
            student_info: 学生信息（可选）
            rag_rules: RAG检索到的规则（可选）
            
        Returns:
            包含分类结果和分数的字典
            {
                "category": "A" | "C",  # 证书类别
                "score": float,  # 分数
                "reason": str,  # 分类原因
                "details": dict,  # 详细信息
                "rag_used": bool,  # 是否使用了RAG
                "rag_rules": list,  # RAG规则列表
                "scoring_rubric": dict  # 评分标准
            }
        """
        try:
            # 如果启用RAG，使用大模型进行分类和算分
            if self.rag_client and settings.RAG_ENABLED:
                return await self._classify_with_rag(
                    certificate_text,
                    certificate_info,
                    student_info,
                    rag_rules
                )
            else:
                # 使用规则引擎进行分类
                return await self._classify_with_rules(
                    certificate_text,
                    certificate_info,
                    rag_rules
                )
                
        except Exception as e:
            logger.error(f"证书分类和算分失败: {e}", exc_info=True)
            # 返回默认值
            return {
                "category": "C",  # 默认C类
                "score": 0.0,
                "reason": f"分类失败: {str(e)}",
                "details": {}
            }
    
    async def _classify_with_rag(
        self,
        certificate_text: str,
        certificate_info: Optional[Dict[str, Any]],
        student_info: Optional[Dict[str, Any]],
        rag_rules: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """使用RAG大模型进行分类和算分"""
        try:
            if rag_rules:
                score_result = await self.rag_client.calculate_score(
                    certificate_text=certificate_text,
                    student_info=student_info,
                    rag_rules=rag_rules
                )
            else:
                score_result = await self.rag_client.calculate_score(
                    certificate_text=certificate_text,
                    student_info=student_info
                )
            
            category = score_result.get("category", "C")
            score = float(score_result.get("score", 0.0))
            reason = score_result.get("reason", "大模型自动分类")
            confidence = score_result.get("confidence", 0.0)
            retrieved_rag_rules = score_result.get("rag_rules", rag_rules or [])
            rag_used = score_result.get("rag_used", bool(rag_rules))

            # Normalize category to standard A/C format
            original_category = category
            if category not in ["A", "C"]:
                # If RAG returns a descriptive name, treat as valid and determine type by score
                if score >= 1.0:
                    # Competition/certificates with positive scores are typically A-class
                    category = "A"
                else:
                    category = "A" if score >= 10.0 else "C"

            # Use RAG score directly if it's reasonable (>0), otherwise fall back to rule engine
            if score == 0.0 or not retrieved_rag_rules:
                logger.warning(f"RAG returned invalid result (original_category={original_category}, score={score}, rules={len(retrieved_rag_rules)}), falling back to rule engine")
                return await self._classify_with_rules(certificate_text, certificate_info)

            # If RAG returned a good score, use it directly (don't recalculate)
            if score > 0:
                logger.info(f"Using RAG result: category={category}, score={score} (from RAG response)")
                scoring_rubric = self._generate_scoring_rubric(
                    category=category,
                    score=score,
                    rag_rules=retrieved_rag_rules,
                    certificate_info=certificate_info
                )

                return {
                    "category": category,
                    "score": score,  # Keep the RAG score!
                    "reason": f"RAG智能评分{f'({original_category})' if original_category != category else ''}: {reason}",
                    "confidence": confidence,
                    "rag_rules": retrieved_rag_rules,
                    "rag_used": rag_used,
                    "details": score_result.get("details", {}),
                    "method": "rag",
                    "scoring_rubric": scoring_rubric
                }
            
            scoring_rubric = self._generate_scoring_rubric(
                category=category,
                score=score,
                rag_rules=retrieved_rag_rules,
                certificate_info=certificate_info
            )
            
            return {
                "category": category,
                "score": score,
                "reason": reason,
                "confidence": confidence,
                "rag_rules": retrieved_rag_rules,
                "rag_used": rag_used,
                "details": score_result.get("details", {}),
                "method": "rag",
                "scoring_rubric": scoring_rubric
            }
            
        except Exception as e:
            logger.warning(f"RAG分类失败，使用规则引擎: {e}")
            return await self._classify_with_rules(certificate_text, certificate_info)
    
    async def _classify_with_rules(
        self,
        certificate_text: str,
        certificate_info: Optional[Dict[str, Any]],
        rag_rules: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """使用规则引擎进行分类和算分"""
        
        a_keywords = [
            "竞赛", "比赛", "获奖", "一等奖", "二等奖", "三等奖",
            "优秀", "卓越", "创新", "科研", "论文", "专利",
            "国家级", "省级", "市级", "国际", "世界",
            "数学建模", "ACM", "挑战杯", "互联网+",
            "创新创业", "科研项目", "发明专利",
            "蓝桥杯", "程序设计", "软件", "信息技术"
        ]
        
        c_keywords = [
            "志愿服务", "社会实践", "公益活动", "志愿者",
            "社会实践", "实习", "工作", "社团", "学生工作",
            "优秀学生", "优秀团员", "优秀干部", "三好学生",
            "奖学金", "助学金", "文体活动", "体育", "文艺"
        ]
        
        text_lower = certificate_text.lower()
        
        a_score = sum(1 for keyword in a_keywords if keyword in text_lower)
        c_score = sum(1 for keyword in c_keywords if keyword in text_lower)
        
        title = ""
        level = ""
        if certificate_info:
            title = certificate_info.get("title", "").lower()
            level = certificate_info.get("level", "").lower()
        
        category = "A" if a_score > c_score else "C"
        
        if category == "A":
            base_score = 5.0
            if "国家级" in text_lower or "国际" in text_lower:
                base_score = 15.0
            elif "省级" in text_lower:
                base_score = 10.0
            elif "市级" in text_lower or "校级" in text_lower:
                base_score = 5.0
            
            if "一等奖" in text_lower or "特等奖" in text_lower:
                base_score *= 1.5
            elif "二等奖" in text_lower:
                base_score *= 1.2
            elif "三等奖" in text_lower:
                base_score *= 1.0
            else:
                base_score *= 0.8
            
            score = min(base_score, 20.0)
        else:
            base_score = 2.0
            if "优秀" in text_lower or "卓越" in text_lower:
                base_score = 5.0
            elif "良好" in text_lower:
                base_score = 3.0
            
            score = min(base_score, 10.0)
        
        matched_rules = []
        if rag_rules:
            for rule in rag_rules:
                rule_keywords = rule.get("keywords", [])
                if any(keyword in text_lower for keyword in rule_keywords):
                    matched_rules.append(rule)
        
        scoring_rubric = self._generate_scoring_rubric(
            category=category,
            score=score,
            rag_rules=rag_rules or [],
            certificate_info=certificate_info
        )
        
        return {
            "category": category,
            "score": score,
            "reason": f"规则引擎分类: A类匹配{a_score}个关键词, C类匹配{c_score}个关键词",
            "details": {
                "a_keywords_matched": a_score,
                "c_keywords_matched": c_score,
                "title": title,
                "level": level,
                "matched_rules": matched_rules
            },
            "method": "rules",
            "rag_used": bool(rag_rules),
            "rag_rules": rag_rules or [],
            "scoring_rubric": scoring_rubric
        }
    
    def _generate_scoring_rubric(
        self,
        category: str,
        score: float,
        rag_rules: List[Dict],
        certificate_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成评分标准
        
        Args:
            category: 证书类别
            score: 分数
            rag_rules: RAG规则列表
            certificate_info: 证书信息
            
        Returns:
            评分标准字典
        """
        category_definition = {
            "A": "A类证书：竞赛、科研、创新类证书，包括学科竞赛获奖、科研项目、专利、论文等",
            "C": "C类证书：社会活动、志愿服务类证书，包括社会实践、志愿服务、学生工作、文体活动等"
        }
        
        score_range = {
            "A": {"min": 0.0, "max": 20.0, "description": "A类证书分数范围：0-20分"},
            "C": {"min": 0.0, "max": 10.0, "description": "C类证书分数范围：0-10分"}
        }
        
        current_score_info = {
            "score": score,
            "category": category,
            "percentage": round(score / score_range[category]["max"] * 100, 2) if score_range[category]["max"] > 0 else 0
        }
        
        scoring_criteria = []
        if category == "A":
            scoring_criteria = [
                {"level": "国家级/国际级", "base_score": 15.0, "multiplier": "1.0-1.5"},
                {"level": "省级", "base_score": 10.0, "multiplier": "1.0-1.5"},
                {"level": "市级/校级", "base_score": 5.0, "multiplier": "1.0-1.5"},
                {"award": "一等奖/特等奖", "multiplier": 1.5},
                {"award": "二等奖", "multiplier": 1.2},
                {"award": "三等奖", "multiplier": 1.0}
            ]
        else:
            scoring_criteria = [
                {"level": "优秀/卓越", "base_score": 5.0},
                {"level": "良好", "base_score": 3.0},
                {"level": "一般", "base_score": 2.0}
            ]
        
        matched_rules = []
        for rule in rag_rules:
            matched_rules.append({
                "rule_name": rule.get("name", "未命名规则"),
                "rule_score": rule.get("score", 0),
                "rule_category": rule.get("category", "unknown"),
                "description": rule.get("description", "")
            })
        
        return {
            "category_definition": category_definition.get(category, "未知类别"),
            "score_range": score_range.get(category, {}),
            "current_score": current_score_info,
            "scoring_criteria": scoring_criteria,
            "matched_rules": matched_rules
        }
    
    async def batch_classify_and_calculate(
        self,
        certificates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量分类和算分
        
        Args:
            certificates: 证书列表，每个证书包含:
                - certificate_text: 证书文本
                - certificate_info: 证书信息（可选）
                - student_info: 学生信息（可选）
                
        Returns:
            分类结果列表
        """
        results = []
        
        for cert in certificates:
            try:
                result = await self.classify_and_calculate_score(
                    certificate_text=cert.get("certificate_text", ""),
                    certificate_info=cert.get("certificate_info"),
                    student_info=cert.get("student_info")
                )
                
                # 添加原始证书信息
                result["certificate_data"] = cert
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量分类证书失败: {e}")
                results.append({
                    "category": "C",
                    "score": 0.0,
                    "reason": f"处理失败: {str(e)}",
                    "details": {},
                    "certificate_data": cert
                })
        
        return results


# 全局单例
_certificate_service_instance: Optional[CertificateClassificationService] = None


def get_certificate_service() -> CertificateClassificationService:
    """获取证书分类服务实例（单例）"""
    global _certificate_service_instance
    
    if _certificate_service_instance is None:
        _certificate_service_instance = CertificateClassificationService()
    
    return _certificate_service_instance

