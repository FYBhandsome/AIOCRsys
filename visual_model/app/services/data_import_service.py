#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测数据导入服务

负责从Excel文件导入学生综测数据，包括：
- 学生基本信息
- 学业成绩
- 综测成绩
- 加减分明细
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from app.models.tortoise_models import (
    Student, Class, AcademicScore, ComprehensiveScore, 
    ComprehensiveScoreConfig, ScoreDetail, Certificate
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class DataImportService:
    """综测数据导入服务"""
    
    COLUMN_MAPPING = {
        '总排名': 'rank',
        '专业': 'major',
        '班级': 'class_name',
        '姓名': 'student_name',
        '学号': 'student_id',
        'A1—基础分': 'a1_score',
        'A2—附加分': 'a2_score',
        'A3—扣罚分': 'a3_score',
        '思想道德素质(A)总分': 'a_total_score',
        '思想道德素质(A)总分20%': 'a_weighted_score',
        '学习成绩': 'b_raw_score',
        '学习成绩70%': 'b_weighted_score',
        'C1—科技类竞赛项目': 'c1_score',
        'C2—体育竞技项目': 'c2_score',
        'C3—文化类竞赛项目': 'c3_score',
        'C4—创新创业实践项目': 'c4_score',
        '素质拓展（C）总分': 'c_total_score',
        '素质拓展（C）总分10%': 'c_weighted_score',
        '综合测评总成绩': 'total_score',
    }
    
    CATEGORY_MAPPING = {
        'A1': {'name': '思想道德素质-基础分', 'description': 'A1类基础分'},
        'A2': {'name': '思想道德素质-附加分', 'description': 'A2类附加分'},
        'A3': {'name': '思想道德素质-扣罚分', 'description': 'A3类扣罚分'},
        'C1': {'name': '科技类竞赛项目', 'description': 'C1类科技竞赛'},
        'C2': {'name': '体育竞技项目', 'description': 'C2类体育竞技'},
        'C3': {'name': '文化类竞赛项目', 'description': 'C3类文化竞赛'},
        'C4': {'name': '创新创业实践项目', 'description': 'C4类创新创业'},
    }
    
    def __init__(self):
        self.import_stats = {
            'students_created': 0,
            'students_updated': 0,
            'scores_created': 0,
            'scores_updated': 0,
            'details_created': 0,
            'errors': []
        }
    
    def reset_stats(self):
        """重置导入统计"""
        self.import_stats = {
            'students_created': 0,
            'students_updated': 0,
            'scores_created': 0,
            'scores_updated': 0,
            'details_created': 0,
            'errors': []
        }
    
    async def import_from_excel(
        self, 
        file_path: str, 
        academic_year: str = None,
        semester: str = None,
        class_id: str = None,
        create_class: bool = True
    ) -> Dict[str, Any]:
        """
        从Excel文件导入综测数据
        
        Args:
            file_path: Excel文件路径
            academic_year: 学年，如 "2024-2025"
            semester: 学期，如 "1" 或 "2"
            class_id: 班级ID，如 "230521"
            create_class: 是否自动创建班级
            
        Returns:
            导入结果统计
        """
        self.reset_stats()
        
        try:
            xl = pd.ExcelFile(file_path)
            
            if '综合测评计算表' in xl.sheet_names:
                await self._import_main_sheet(
                    xl, academic_year, semester, class_id, create_class
                )
            
            if '加减分说明' in xl.sheet_names:
                await self._import_detail_sheet(
                    xl, academic_year, semester
                )
            
            logger.info(f"数据导入完成: {self.import_stats}")
            return {
                'success': True,
                'stats': self.import_stats,
                'message': f"导入完成：创建学生{self.import_stats['students_created']}人，"
                          f"更新学生{self.import_stats['students_updated']}人，"
                          f"创建成绩{self.import_stats['scores_created']}条，"
                          f"更新成绩{self.import_stats['scores_updated']}条"
            }
            
        except Exception as e:
            logger.error(f"导入数据失败: {e}", exc_info=True)
            self.import_stats['errors'].append(str(e))
            return {
                'success': False,
                'stats': self.import_stats,
                'message': f"导入失败: {str(e)}"
            }
    
    async def _import_main_sheet(
        self, 
        xl: pd.ExcelFile, 
        academic_year: str,
        semester: str,
        class_id: str,
        create_class: bool
    ):
        """导入主数据表"""
        df = pd.read_excel(xl, sheet_name='综合测评计算表', header=2)
        
        df.columns = [self.COLUMN_MAPPING.get(str(col).strip(), str(col).strip()) 
                      for col in df.columns]
        
        df = df.dropna(subset=['student_id', 'student_name'])
        df = df[df['student_id'].apply(lambda x: str(x).replace('.0', '').isdigit())]
        
        if df.empty:
            logger.warning("Excel文件中没有有效的学生数据")
            return
        
        first_row = df.iloc[0]
        major = str(first_row.get('major', '未知专业'))
        class_name = str(first_row.get('class_name', class_id or '未知班级'))
        
        if create_class and class_id:
            await self._ensure_class_exists(class_id, class_name, major)
        
        for idx, row in df.iterrows():
            try:
                await self._import_student_row(row, academic_year, semester, class_id, major)
            except Exception as e:
                student_id = row.get('student_id', 'unknown')
                logger.error(f"导入学生 {student_id} 数据失败: {e}")
                self.import_stats['errors'].append(f"学生{student_id}: {str(e)}")
    
    async def _ensure_class_exists(self, class_id: str, class_name: str, major: str):
        """确保班级存在"""
        try:
            existing_class = await Class.get_or_none(id=class_id)
            if not existing_class:
                await Class.create(
                    id=class_id,
                    name=class_name,
                    major=major,
                    grade=f"20{class_id[:2]}" if len(class_id) >= 2 else "未知年级",
                    college="计算机学院"
                )
                logger.info(f"创建班级: {class_id} - {class_name}")
        except Exception as e:
            logger.warning(f"创建班级失败: {e}")
    
    async def _import_student_row(
        self, 
        row: pd.Series, 
        academic_year: str,
        semester: str,
        class_id: str,
        major: str
    ):
        """导入单个学生的数据"""
        student_id = str(row.get('student_id', '')).replace('.0', '')
        student_name = str(row.get('student_name', ''))
        
        if not student_id or not student_name:
            return
        
        student = await Student.get_or_none(id=student_id)
        
        if student:
            student.name = student_name
            student.major = major
            student.class_name = class_id or row.get('class_name', '')
            student.total_score = float(row.get('total_score', 0) or 0)
            await student.save()
            self.import_stats['students_updated'] += 1
        else:
            student = await Student.create(
                id=student_id,
                name=student_name,
                college="计算机学院",
                major=major,
                class_name=class_id or str(row.get('class_name', '')),
                grade=f"20{student_id[:2]}" if len(student_id) >= 2 else "未知年级",
                total_score=float(row.get('total_score', 0) or 0)
            )
            self.import_stats['students_created'] += 1
        
        await self._import_comprehensive_score(student_id, row, academic_year, semester)
    
    async def _import_comprehensive_score(
        self,
        student_id: str,
        row: pd.Series,
        academic_year: str,
        semester: str
    ):
        """导入综测成绩"""
        if not academic_year:
            academic_year = "2024-2025"
        if not semester:
            semester = "1"
        
        a1 = float(row.get('a1_score', 0) or 0)
        a2 = float(row.get('a2_score', 0) or 0)
        a3 = float(row.get('a3_score', 0) or 0)
        a_total = float(row.get('a_total_score', 0) or 0)
        
        b_raw = float(row.get('b_raw_score', 0) or 0)
        b_weighted = float(row.get('b_weighted_score', 0) or 0)
        
        c1 = float(row.get('c1_score', 0) or 0)
        c2 = float(row.get('c2_score', 0) or 0)
        c3 = float(row.get('c3_score', 0) or 0)
        c4 = float(row.get('c4_score', 0) or 0)
        c_total = float(row.get('c_total_score', 0) or 0)
        
        total = float(row.get('total_score', 0) or 0)
        
        existing = await ComprehensiveScore.get_or_none(
            student_id=student_id,
            semester=semester,
            academic_year=academic_year
        )
        
        if existing:
            existing.a1_score = a1
            existing.a2_score = a2
            existing.a3_score = a3
            existing.a_total_score = a_total
            existing.b_total_score = b_raw
            existing.c1_score = c1
            existing.c2_score = c2
            existing.c3_score = c3
            existing.c4_score = c4
            existing.c_total_score = c_total
            existing.total_score = total
            await existing.save()
            self.import_stats['scores_updated'] += 1
        else:
            await ComprehensiveScore.create(
                student_id=student_id,
                semester=semester,
                academic_year=academic_year,
                a1_score=a1,
                a2_score=a2,
                a3_score=a3,
                a_total_score=a_total,
                b_total_score=b_raw,
                c1_score=c1,
                c2_score=c2,
                c3_score=c3,
                c4_score=c4,
                c_total_score=c_total,
                total_score=total
            )
            self.import_stats['scores_created'] += 1
    
    async def _import_detail_sheet(
        self, 
        xl: pd.ExcelFile, 
        academic_year: str,
        semester: str
    ):
        """导入加减分明细表"""
        df = pd.read_excel(xl, sheet_name='加减分说明', header=0)
        
        for idx, row in df.iterrows():
            try:
                await self._import_detail_row(row, academic_year, semester)
            except Exception as e:
                logger.error(f"导入明细行 {idx} 失败: {e}")
    
    async def _import_detail_row(
        self, 
        row: pd.Series,
        academic_year: str,
        semester: str
    ):
        """导入单行加减分明细"""
        student_name = row.iloc[2] if len(row) > 2 else None
        if pd.isna(student_name):
            return
        
        student_id = await self._find_student_id_by_name(str(student_name))
        if not student_id:
            return
        
        if not academic_year:
            academic_year = "2024-2025"
        if not semester:
            semester = "1"
        
        detail_columns = [
            (3, 'A1', 'A1—基础分'),
            (4, 'A2', 'A2—附加分'),
            (5, 'A3', 'A3—扣罚分'),
            (6, 'C1', 'C1—科技类竞赛项目'),
            (7, 'C2', 'C2—体育竞技项目'),
            (8, 'C3', 'C3—文化类竞赛项目'),
            (9, 'C4', 'C4—创新创业实践项目'),
        ]
        
        for col_idx, category, item_name in detail_columns:
            if len(row) > col_idx:
                detail_text = row.iloc[col_idx]
                if pd.notna(detail_text) and str(detail_text).strip():
                    await self._parse_and_create_detail(
                        student_id, 
                        academic_year, 
                        semester,
                        category, 
                        item_name, 
                        str(detail_text)
                    )
    
    async def _find_student_id_by_name(self, name: str) -> Optional[str]:
        """根据姓名查找学号"""
        try:
            student = await Student.filter(name=name).first()
            return student.id if student else None
        except Exception:
            return None
    
    async def _parse_and_create_detail(
        self,
        student_id: str,
        academic_year: str,
        semester: str,
        category: str,
        item_name: str,
        detail_text: str
    ):
        """解析并创建加减分明细"""
        import re
        
        items = re.split(r'[，,\n]+', detail_text)
        
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            score_match = re.search(r'([+-]?\d+\.?\d*)\s*分', item)
            score = float(score_match.group(1)) if score_match else 0
            
            if score == 0:
                score_match2 = re.search(r'([+-]?\d+\.?\d*)', item.split('+')[-1] if '+' in item else item)
                if score_match2:
                    score = float(score_match2.group(1))
            
            existing = await ScoreDetail.filter(
                student_id=student_id,
                academic_year=academic_year,
                semester=semester,
                category_type=category,
                item_name=item[:255]
            ).first()
            
            if not existing:
                await ScoreDetail.create(
                    student_id=student_id,
                    academic_year=academic_year,
                    semester=semester,
                    category_type=category,
                    item_name=item[:255],
                    score=score,
                    description=detail_text,
                    source='import'
                )
                self.import_stats['details_created'] += 1
    
    async def get_import_template(self) -> Dict[str, Any]:
        """获取导入模板信息"""
        return {
            'columns': list(self.COLUMN_MAPPING.keys()),
            'categories': self.CATEGORY_MAPPING,
            'required_fields': ['学号', '姓名', '班级'],
            'optional_fields': ['专业', 'A1—基础分', 'A2—附加分', '学习成绩', 'C1—科技类竞赛项目']
        }


data_import_service = DataImportService()


def get_data_import_service() -> DataImportService:
    """获取数据导入服务实例"""
    return data_import_service
