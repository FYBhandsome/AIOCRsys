#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测成绩计算服务

根据配置的权重和学业成绩，自动计算学生的综测总成绩。
"""

from typing import Optional, Dict, Any
from app.core.logger import logger
from app.core.exceptions import DatabaseException


class ComprehensiveScoreCalculationService:
    """综测成绩计算服务"""
    
    def __init__(self):
        """初始化服务"""
        logger.info("综测成绩计算服务已初始化")
    
    def calculate_comprehensive_score(
        self,
        academic_score: Any,  # AcademicScore model instance
        config: Any,  # ComprehensiveScoreConfig model instance
        a_total_score: float = 0.0,
        c_total_score: float = 0.0
    ) -> Dict[str, float]:
        """计算综测总成绩
        
        Args:
            academic_score: 学业成绩对象
            config: 综测配置对象
            a_total_score: A类材料总成绩（0-100）
            c_total_score: C类材料总成绩（0-100）
            
        Returns:
            包含各部分成绩的字典
        """
        try:
            # 1. 获取学业成绩（B类）
            b_score = self._get_academic_score_value(academic_score, config)
            
            # 2. 计算各部分的加权成绩
            a_weighted = a_total_score * (config.a_weight / 100.0)
            b_weighted = b_score * (config.b_weight / 100.0)
            c_weighted = c_total_score * (config.c_weight / 100.0)
            
            # 3. 计算综测总分
            total_score = a_weighted + b_weighted + c_weighted
            
            logger.info(
                f"综测成绩计算: A类={a_total_score:.2f}*{config.a_weight}%={a_weighted:.2f}, "
                f"B类={b_score:.2f}*{config.b_weight}%={b_weighted:.2f}, "
                f"C类={c_total_score:.2f}*{config.c_weight}%={c_weighted:.2f}, "
                f"总分={total_score:.2f}"
            )
            
            return {
                "a_total_score": a_total_score,
                "a_weighted_score": a_weighted,
                "b_total_score": b_score,
                "b_weighted_score": b_weighted,
                "c_total_score": c_total_score,
                "c_weighted_score": c_weighted,
                "total_score": total_score,
                "config_id": config.id,
                "config_name": config.name
            }
        
        except Exception as e:
            logger.error(f"计算综测成绩失败: {e}", exc_info=True)
            raise DatabaseException(f"计算综测成绩失败: {str(e)}")
    
    def _get_academic_score_value(self, academic_score: Any, config: Any) -> float:
        """根据配置获取学业成绩值
        
        Args:
            academic_score: 学业成绩对象
            config: 综测配置对象
            
        Returns:
            转换后的学业成绩值（百分制）
        """
        field_name = config.academic_score_field
        scale = config.academic_score_scale
        
        # 获取字段值
        if not hasattr(academic_score, field_name):
            logger.warning(f"学业成绩对象没有字段: {field_name}，使用默认值0")
            return 0.0
        
        value = getattr(academic_score, field_name, 0.0)
        
        # 应用缩放系数
        scaled_value = value * scale
        
        # 确保在0-100范围内
        scaled_value = max(0.0, min(100.0, scaled_value))
        
        logger.debug(
            f"学业成绩字段={field_name}, 原始值={value:.2f}, "
            f"缩放系数={scale}, 转换后={scaled_value:.2f}"
        )
        
        return scaled_value
    
    def batch_calculate_comprehensive_scores(
        self,
        academic_scores: list,
        config: Any,
        a_scores_map: Dict[str, float] = None,
        c_scores_map: Dict[str, float] = None
    ) -> Dict[str, Dict[str, float]]:
        """批量计算综测成绩
        
        Args:
            academic_scores: 学业成绩对象列表
            config: 综测配置对象
            a_scores_map: 学号->A类成绩的映射
            c_scores_map: 学号->C类成绩的映射
            
        Returns:
            学号->成绩字典的映射
        """
        a_scores_map = a_scores_map or {}
        c_scores_map = c_scores_map or {}
        
        results = {}
        
        for academic_score in academic_scores:
            student_id = academic_score.student_id
            a_score = a_scores_map.get(student_id, 0.0)
            c_score = c_scores_map.get(student_id, 0.0)
            
            result = self.calculate_comprehensive_score(
                academic_score=academic_score,
                config=config,
                a_total_score=a_score,
                c_total_score=c_score
            )
            
            results[student_id] = result
        
        logger.info(f"批量计算了 {len(results)} 个学生的综测成绩")
        
        return results
    
    def get_field_info(self, field_name: str) -> Dict[str, Any]:
        """获取学业成绩字段的信息（中文版）
        
        Args:
            field_name: 字段名（英文）
            
        Returns:
            字段信息字典（包含中文标签）
        """
        field_infos = {
            "arithmetic_average": {
                "value": "arithmetic_average",
                "label": "算术平均分",
                "english_name": "Arithmetic Average",
                "description": "所有课程成绩的算术平均值，不考虑学分权重",
                "default_scale": 1.0,
                "range": "0-100",
                "unit": "分"
            },
            "weighted_average": {
                "value": "weighted_average",
                "label": "学分加权平均分",
                "english_name": "Weighted Average",
                "description": "按学分加权的平均分，反映课程学分对总成绩的影响",
                "default_scale": 1.0,
                "range": "0-100",
                "unit": "分",
                "recommended": True
            },
            "average_gpa": {
                "value": "average_gpa",
                "label": "平均绩点",
                "english_name": "Average GPA",
                "description": "GPA平均值（4分制），需转换为百分制使用",
                "default_scale": 25.0,  # 4分制转100分制
                "range": "0-4",
                "unit": "GPA"
            },
            "average_credit_gpa": {
                "value": "average_credit_gpa",
                "label": "平均学分绩点",
                "english_name": "Average Credit GPA",
                "description": "按学分加权的GPA（4分制），需转换为百分制使用",
                "default_scale": 25.0,  # 4分制转100分制
                "range": "0-4",
                "unit": "GPA"
            },
            "credit_gpa_sum": {
                "value": "credit_gpa_sum",
                "label": "学分绩点和",
                "english_name": "Credit GPA Sum",
                "description": "总学分绩点和，适用于特定计算场景",
                "default_scale": 1.0,
                "range": "varies",
                "unit": "点"
            }
        }
        
        return field_infos.get(field_name, {
            "value": field_name,
            "label": field_name,
            "english_name": field_name,
            "description": "未知字段",
            "default_scale": 1.0,
            "range": "unknown",
            "unit": "未知"
        })


# 全局单例
_comprehensive_score_calculation_service: Optional[ComprehensiveScoreCalculationService] = None


def get_comprehensive_score_calculation_service() -> ComprehensiveScoreCalculationService:
    """获取综测成绩计算服务单例"""
    global _comprehensive_score_calculation_service
    if _comprehensive_score_calculation_service is None:
        _comprehensive_score_calculation_service = ComprehensiveScoreCalculationService()
    return _comprehensive_score_calculation_service

