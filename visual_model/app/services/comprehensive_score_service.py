#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测成绩计算服务

负责计算学生的综合测评成绩，包括：
- A类材料成绩（思想道德素质）
- B类材料成绩（学习成绩）
- C类材料成绩（素质拓展）

优化版本：
- 集成缓存机制
- 批量数据库查询
- 并行计算支持
- 性能监控
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from app.models.tortoise_models import (
    Student, Class, AcademicScore, ComprehensiveScore, 
    ComprehensiveScoreConfig, ScoreDetail, Certificate
)
from app.core.logger import get_logger
from app.core.cache_service import get_cache_service, cached

logger = get_logger(__name__)


class ComprehensiveScoreService:
    """综测成绩计算服务
    
    优化版本：
    - 缓存机制：减少重复计算
    - 批量查询：优化数据库访问
    - 并行计算：加速班级成绩计算
    - 性能监控：记录计算耗时
    """
    
    DEFAULT_WEIGHTS = {
        'a_weight': 20.0,
        'b_weight': 70.0,
        'c_weight': 10.0
    }
    
    CERTIFICATE_SCORE_RULES = {
        '国家级': {'A': 15, 'C': 12},
        '省级': {'A': 10, 'C': 8},
        '校级': {'A': 6, 'C': 5},
        '院级': {'A': 4, 'C': 3},
    }
    
    ENGLISH_SCORE_RULES = {
        '四级': {'pass': 425, 'scores': {425: 3, 500: 4, 550: 5, 600: 6}},
        '六级': {'pass': 425, 'scores': {425: 5, 500: 6, 550: 7, 600: 8}},
    }
    
    def __init__(self):
        self._cache = get_cache_service()
        self._stats = {
            "total_calculations": 0,
            "cache_hits": 0,
            "total_time_ms": 0
        }
    
    async def calculate_student_score(
        self,
        student_id: str,
        academic_year: str,
        semester: str,
        config_id: int = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        计算单个学生的综测成绩
        
        Args:
            student_id: 学号
            academic_year: 学年
            semester: 学期
            config_id: 配置ID（可选）
            force_refresh: 是否强制刷新缓存
            
        Returns:
            计算结果
        """
        start_time = time.time()
        self._stats["total_calculations"] += 1
        
        cache_key = f"score_{student_id}_{academic_year}_{semester}_{config_id}"
        
        if not force_refresh:
            cached_result = self._cache.get('comprehensive_score', cache_key)
            if cached_result is not None:
                self._stats["cache_hits"] += 1
                elapsed_ms = (time.time() - start_time) * 1000
                self._stats["total_time_ms"] += elapsed_ms
                logger.debug(f"缓存命中: {cache_key}, 耗时: {elapsed_ms:.2f}ms")
                return cached_result
        
        student = await Student.get_or_none(id=student_id)
        if not student:
            return {'success': False, 'message': f'学生不存在: {student_id}'}
        
        config = await self._get_config(config_id)
        
        a_score, b_score, c_score = await asyncio.gather(
            self._calculate_a_score(student_id, academic_year, semester),
            self._calculate_b_score(student_id, academic_year, semester, config),
            self._calculate_c_score(student_id, academic_year, semester)
        )
        
        a_weighted = a_score['total'] * config.a_weight / 100
        b_weighted = b_score['score'] * config.b_weight / 100
        c_weighted = c_score['total'] * config.c_weight / 100
        
        total_score = a_weighted + b_weighted + c_weighted
        
        comp_score, created = await ComprehensiveScore.update_or_create(
            student_id=student_id,
            semester=semester,
            academic_year=academic_year,
            defaults={
                'a1_score': a_score['a1'],
                'a2_score': a_score['a2'],
                'a3_score': a_score['a3'],
                'a_total_score': a_score['total'],
                'b_total_score': b_score['score'],
                'c1_score': c_score['c1'],
                'c2_score': c_score['c2'],
                'c3_score': c_score['c3'],
                'c4_score': c_score['c4'],
                'c_total_score': c_score['total'],
                'total_score': total_score,
                'details': {
                    'a_details': a_score['details'],
                    'b_details': b_score['details'],
                    'c_details': c_score['details']
                }
            }
        )
        
        student.total_score = total_score
        await student.save()
        
        result = {
            'success': True,
            'student_id': student_id,
            'student_name': student.name,
            'scores': {
                'a_score': a_score,
                'b_score': b_score,
                'c_score': c_score,
                'a_weighted': a_weighted,
                'b_weighted': b_weighted,
                'c_weighted': c_weighted,
                'total_score': total_score
            },
            'created': created
        }
        
        self._cache.set('comprehensive_score', cache_key, result, ttl=600.0)
        
        elapsed_ms = (time.time() - start_time) * 1000
        self._stats["total_time_ms"] += elapsed_ms
        logger.debug(f"计算学生 {student_id} 成绩完成，耗时: {elapsed_ms:.2f}ms")
        
        return result
    
    async def calculate_class_scores(
        self,
        class_id: str,
        academic_year: str,
        semester: str,
        config_id: int = None
    ) -> Dict[str, Any]:
        """
        计算班级所有学生的综测成绩
        
        Args:
            class_id: 班级ID
            academic_year: 学年
            semester: 学期
            config_id: 配置ID
            
        Returns:
            计算结果统计
        """
        students = await Student.filter(class_name=class_id).all()
        
        if not students:
            return {'success': False, 'message': f'班级不存在或没有学生: {class_id}'}
        
        config = await self._get_config(config_id)
        
        student_ids = [s.id for s in students]
        
        score_details = await ScoreDetail.filter(
            student_id__in=student_ids,
            academic_year=academic_year,
            semester=semester
        ).all()
        
        details_by_student: Dict[str, List[ScoreDetail]] = {}
        for detail in score_details:
            if detail.student_id not in details_by_student:
                details_by_student[detail.student_id] = []
            details_by_student[detail.student_id].append(detail)
        
        academic_scores = await AcademicScore.filter(
            student_id__in=student_ids,
            academic_year=academic_year
        ).all()
        
        academic_by_student: Dict[str, AcademicScore] = {
            a.student_id: a for a in academic_scores
        }
        
        results = []
        success_count = 0
        error_count = 0
        
        for student in students:
            try:
                student_details = details_by_student.get(student.id, [])
                academic = academic_by_student.get(student.id)
                
                a_score = self._calculate_a_score_from_details(student_details)
                b_score = self._calculate_b_score_from_academic(academic, config)
                c_score = self._calculate_c_score_from_details(student_details)
                
                a_weighted = a_score['total'] * config.a_weight / 100
                b_weighted = b_score['score'] * config.b_weight / 100
                c_weighted = c_score['total'] * config.c_weight / 100
                
                total_score = a_weighted + b_weighted + c_weighted
                
                await ComprehensiveScore.update_or_create(
                    student_id=student.id,
                    semester=semester,
                    academic_year=academic_year,
                    defaults={
                        'a1_score': a_score['a1'],
                        'a2_score': a_score['a2'],
                        'a3_score': a_score['a3'],
                        'a_total_score': a_score['total'],
                        'b_total_score': b_score['score'],
                        'c1_score': c_score['c1'],
                        'c2_score': c_score['c2'],
                        'c3_score': c_score['c3'],
                        'c4_score': c_score['c4'],
                        'c_total_score': c_score['total'],
                        'total_score': total_score,
                        'details': {
                            'a_details': a_score['details'],
                            'b_details': b_score['details'],
                            'c_details': c_score['details']
                        }
                    }
                )
                
                student.total_score = total_score
                await student.save()
                
                results.append({
                    'success': True,
                    'student_id': student.id,
                    'student_name': student.name,
                    'total_score': total_score
                })
                success_count += 1
                
            except Exception as e:
                logger.error(f"计算学生 {student.id} 成绩失败: {e}")
                results.append({
                    'success': False,
                    'student_id': student.id,
                    'message': str(e)
                })
                error_count += 1
        
        ranked_results = await self._rank_students(class_id, academic_year, semester)
        
        return {
            'success': True,
            'class_id': class_id,
            'academic_year': academic_year,
            'semester': semester,
            'total_students': len(students),
            'success_count': success_count,
            'error_count': error_count,
            'results': results,
            'rankings': ranked_results
        }
    
    def _calculate_a_score_from_details(self, details: List[ScoreDetail]) -> Dict[str, Any]:
        """从明细列表计算A类材料成绩"""
        a1 = 0.0
        a2 = 0.0
        a3 = 0.0
        detail_list = []
        
        for detail in details:
            if detail.category_type == 'A1':
                a1 += detail.score
            elif detail.category_type == 'A2':
                a2 += detail.score
            elif detail.category_type == 'A3':
                a3 += detail.score
            
            if detail.category_type in ['A1', 'A2', 'A3']:
                detail_list.append({
                    'category': detail.category_type,
                    'item': detail.item_name,
                    'score': detail.score
                })
        
        a1 = min(a1, 100)
        total = a1 + a2 + a3
        
        return {
            'a1': a1,
            'a2': a2,
            'a3': a3,
            'total': total,
            'details': detail_list
        }
    
    def _calculate_b_score_from_academic(
        self, 
        academic: Optional[AcademicScore], 
        config: ComprehensiveScoreConfig
    ) -> Dict[str, Any]:
        """从学业成绩计算B类材料成绩"""
        if not academic:
            return {
                'score': 0.0,
                'details': {'message': '未找到学业成绩数据'}
            }
        
        field_name = config.academic_score_field
        score = getattr(academic, field_name, 0) or 0
        score = score * config.academic_score_scale
        
        return {
            'score': score,
            'field_used': field_name,
            'details': {
                'weighted_average': academic.weighted_average,
                'arithmetic_average': academic.arithmetic_average,
                'average_gpa': academic.average_gpa,
                'average_credit_gpa': academic.average_credit_gpa,
                'credit_gpa_sum': academic.credit_gpa_sum,
                'field_used': field_name,
                'scale': config.academic_score_scale
            }
        }
    
    def _calculate_c_score_from_details(self, details: List[ScoreDetail]) -> Dict[str, Any]:
        """从明细列表计算C类材料成绩"""
        c1 = 0.0
        c2 = 0.0
        c3 = 0.0
        c4 = 0.0
        detail_list = []
        
        for detail in details:
            if detail.category_type == 'C1':
                c1 += detail.score
            elif detail.category_type == 'C2':
                c2 += detail.score
            elif detail.category_type == 'C3':
                c3 += detail.score
            elif detail.category_type == 'C4':
                c4 += detail.score
            
            if detail.category_type in ['C1', 'C2', 'C3', 'C4']:
                detail_list.append({
                    'category': detail.category_type,
                    'item': detail.item_name,
                    'score': detail.score
                })
        
        total = c1 + c2 + c3 + c4
        
        return {
            'c1': c1,
            'c2': c2,
            'c3': c3,
            'c4': c4,
            'total': total,
            'details': detail_list
        }
    
    async def _get_config(self, config_id: int = None) -> ComprehensiveScoreConfig:
        """获取综测配置"""
        if config_id:
            config = await ComprehensiveScoreConfig.get_or_none(id=config_id)
            if config:
                return config
        
        config = await ComprehensiveScoreConfig.filter(is_default=True).first()
        if config:
            return config
        
        return await ComprehensiveScoreConfig.create(
            name="默认配置",
            a_weight=20.0,
            b_weight=70.0,
            c_weight=10.0,
            is_default=True,
            is_active=True
        )
    
    async def _calculate_a_score(
        self,
        student_id: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """计算A类材料成绩（思想道德素质）"""
        details = await ScoreDetail.filter(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester,
            category_type__in=['A1', 'A2', 'A3']
        ).all()
        
        a1 = 0.0
        a2 = 0.0
        a3 = 0.0
        detail_list = []
        
        for detail in details:
            if detail.category_type == 'A1':
                a1 += detail.score
            elif detail.category_type == 'A2':
                a2 += detail.score
            elif detail.category_type == 'A3':
                a3 += detail.score
            
            detail_list.append({
                'category': detail.category_type,
                'item': detail.item_name,
                'score': detail.score
            })
        
        a1 = min(a1, 100)
        
        total = a1 + a2 + a3
        
        return {
            'a1': a1,
            'a2': a2,
            'a3': a3,
            'total': total,
            'details': detail_list
        }
    
    async def _calculate_b_score(
        self,
        student_id: str,
        academic_year: str,
        semester: str,
        config: ComprehensiveScoreConfig
    ) -> Dict[str, Any]:
        """计算B类材料成绩（学习成绩）"""
        academic = await AcademicScore.filter(
            student_id=student_id,
            academic_year=academic_year
        ).first()
        
        if not academic:
            return {
                'score': 0.0,
                'details': {'message': '未找到学业成绩数据'}
            }
        
        field_name = config.academic_score_field
        score = getattr(academic, field_name, 0) or 0
        
        score = score * config.academic_score_scale
        
        return {
            'score': score,
            'field_used': field_name,
            'details': {
                'weighted_average': academic.weighted_average,
                'arithmetic_average': academic.arithmetic_average,
                'average_gpa': academic.average_gpa,
                'average_credit_gpa': academic.average_credit_gpa,
                'credit_gpa_sum': academic.credit_gpa_sum,
                'field_used': field_name,
                'scale': config.academic_score_scale
            }
        }
    
    async def _calculate_c_score(
        self,
        student_id: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """计算C类材料成绩（素质拓展）"""
        details = await ScoreDetail.filter(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester,
            category_type__in=['C1', 'C2', 'C3', 'C4']
        ).all()
        
        c1 = 0.0
        c2 = 0.0
        c3 = 0.0
        c4 = 0.0
        detail_list = []
        
        for detail in details:
            if detail.category_type == 'C1':
                c1 += detail.score
            elif detail.category_type == 'C2':
                c2 += detail.score
            elif detail.category_type == 'C3':
                c3 += detail.score
            elif detail.category_type == 'C4':
                c4 += detail.score
            
            detail_list.append({
                'category': detail.category_type,
                'item': detail.item_name,
                'score': detail.score
            })
        
        total = c1 + c2 + c3 + c4
        
        return {
            'c1': c1,
            'c2': c2,
            'c3': c3,
            'c4': c4,
            'total': total,
            'details': detail_list
        }
    
    async def _rank_students(
        self,
        class_id: str,
        academic_year: str,
        semester: str
    ) -> List[Dict[str, Any]]:
        """对学生成绩进行排名"""
        scores = await ComprehensiveScore.filter(
            student__class_name=class_id,
            academic_year=academic_year,
            semester=semester
        ).prefetch_related('student').order_by('-total_score').all()
        
        rankings = []
        for rank, score in enumerate(scores, 1):
            student = score.student
            rankings.append({
                'rank': rank,
                'student_id': score.student_id,
                'student_name': student.name if student else score.student_name,
                'total_score': score.total_score,
                'a_score': score.a_total_score,
                'b_score': score.b_total_score,
                'c_score': score.c_total_score
            })
        
        return rankings
    
    async def add_score_detail(
        self,
        student_id: str,
        academic_year: str,
        semester: str,
        category_type: str,
        item_name: str,
        score: float,
        description: str = None,
        certificate_id: int = None
    ) -> ScoreDetail:
        """添加加减分明细"""
        return await ScoreDetail.create(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester,
            category_type=category_type,
            item_name=item_name,
            score=score,
            description=description,
            certificate_id=certificate_id,
            source='manual'
        )
    
    async def get_student_score_details(
        self,
        student_id: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """获取学生成绩明细"""
        comp_score = await ComprehensiveScore.get_or_none(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester
        )
        
        details = await ScoreDetail.filter(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester
        ).all()
        
        grouped_details = {
            'A1': [], 'A2': [], 'A3': [],
            'C1': [], 'C2': [], 'C3': [], 'C4': []
        }
        
        for detail in details:
            if detail.category_type in grouped_details:
                grouped_details[detail.category_type].append({
                    'id': detail.id,
                    'item_name': detail.item_name,
                    'score': detail.score,
                    'description': detail.description,
                    'source': detail.source
                })
        
        return {
            'comprehensive_score': {
                'a1_score': comp_score.a1_score if comp_score else 0,
                'a2_score': comp_score.a2_score if comp_score else 0,
                'a3_score': comp_score.a3_score if comp_score else 0,
                'a_total_score': comp_score.a_total_score if comp_score else 0,
                'b_total_score': comp_score.b_total_score if comp_score else 0,
                'c1_score': comp_score.c1_score if comp_score else 0,
                'c2_score': comp_score.c2_score if comp_score else 0,
                'c3_score': comp_score.c3_score if comp_score else 0,
                'c4_score': comp_score.c4_score if comp_score else 0,
                'c_total_score': comp_score.c_total_score if comp_score else 0,
                'total_score': comp_score.total_score if comp_score else 0,
            } if comp_score else None,
            'details': grouped_details
        }


comprehensive_score_service = ComprehensiveScoreService()


def get_comprehensive_score_service() -> ComprehensiveScoreService:
    """获取综测成绩计算服务实例"""
    return comprehensive_score_service


def get_comprehensive_score_calculation_service() -> ComprehensiveScoreService:
    """获取综测成绩计算服务实例（别名）"""
    return comprehensive_score_service
