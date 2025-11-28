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
        student_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分类证书并计算分数
        
        Args:
            certificate_text: 证书文本内容
            certificate_info: 证书详细信息（可选）
            student_info: 学生信息（可选）
            
        Returns:
            包含分类结果和分数的字典
            {
                "category": "A" | "C",  # 证书类别
                "score": float,  # 分数
                "reason": str,  # 分类原因
                "details": dict  # 详细信息
            }
        """
        try:
            # 如果启用RAG，使用大模型进行分类和算分
            if self.rag_client and settings.RAG_ENABLED:
                return await self._classify_with_rag(
                    certificate_text,
                    certificate_info,
                    student_info
                )
            else:
                # 使用规则引擎进行分类
                return await self._classify_with_rules(
                    certificate_text,
                    certificate_info
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
        student_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用RAG大模型进行分类和算分"""
        try:
            # 调用RAG计算分数（RAG系统应该返回分类和分数）
            score_result = await self.rag_client.calculate_score(
                certificate_text=certificate_text,
                student_info=student_info
            )
            
            # 解析RAG返回的结果
            # 假设RAG返回格式: {"category": "A"|"C", "score": float, "reason": str, ...}
            category = score_result.get("category", "C")
            score = float(score_result.get("score", 0.0))
            reason = score_result.get("reason", "大模型自动分类")
            
            # 确保category是A或C
            if category not in ["A", "C"]:
                # 根据分数判断类别（A类通常分数更高）
                category = "A" if score >= 10.0 else "C"
            
            return {
                "category": category,
                "score": score,
                "reason": reason,
                "details": score_result,
                "method": "rag"
            }
            
        except Exception as e:
            logger.warning(f"RAG分类失败，使用规则引擎: {e}")
            return await self._classify_with_rules(certificate_text, certificate_info)
    
    async def _classify_with_rules(
        self,
        certificate_text: str,
        certificate_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用规则引擎进行分类和算分"""
        
        # A类证书关键词（竞赛、科研等）
        a_keywords = [
            "竞赛", "比赛", "获奖", "一等奖", "二等奖", "三等奖",
            "优秀", "卓越", "创新", "科研", "论文", "专利",
            "国家级", "省级", "市级", "国际", "世界",
            "数学建模", "ACM", "挑战杯", "互联网+",
            "创新创业", "科研项目", "发明专利"
        ]
        
        # C类证书关键词（社会活动、志愿服务等）
        c_keywords = [
            "志愿服务", "社会实践", "公益活动", "志愿者",
            "社会实践", "实习", "工作", "社团", "学生工作",
            "优秀学生", "优秀团员", "优秀干部", "三好学生",
            "奖学金", "助学金", "文体活动", "体育", "文艺"
        ]
        
        text_lower = certificate_text.lower()
        
        # 计算关键词匹配分数
        a_score = sum(1 for keyword in a_keywords if keyword in text_lower)
        c_score = sum(1 for keyword in c_keywords if keyword in text_lower)
        
        # 从certificate_info中提取信息
        title = ""
        level = ""
        if certificate_info:
            title = certificate_info.get("title", "").lower()
            level = certificate_info.get("level", "").lower()
        
        # 判断类别
        category = "A" if a_score > c_score else "C"
        
        # 计算分数（简单规则）
        if category == "A":
            # A类：根据级别和标题关键词计算
            base_score = 5.0
            if "国家级" in text_lower or "国际" in text_lower:
                base_score = 15.0
            elif "省级" in text_lower:
                base_score = 10.0
            elif "市级" in text_lower or "校级" in text_lower:
                base_score = 5.0
            
            # 根据等级调整
            if "一等奖" in text_lower or "特等奖" in text_lower:
                base_score *= 1.5
            elif "二等奖" in text_lower:
                base_score *= 1.2
            elif "三等奖" in text_lower:
                base_score *= 1.0
            else:
                base_score *= 0.8
            
            score = min(base_score, 20.0)  # 最高20分
        else:
            # C类：分数较低
            base_score = 2.0
            if "优秀" in text_lower or "卓越" in text_lower:
                base_score = 5.0
            elif "良好" in text_lower:
                base_score = 3.0
            
            score = min(base_score, 10.0)  # 最高10分
        
        return {
            "category": category,
            "score": score,
            "reason": f"规则引擎分类: A类匹配{a_score}个关键词, C类匹配{c_score}个关键词",
            "details": {
                "a_keywords_matched": a_score,
                "c_keywords_matched": c_score,
                "title": title,
                "level": level
            },
            "method": "rules"
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

