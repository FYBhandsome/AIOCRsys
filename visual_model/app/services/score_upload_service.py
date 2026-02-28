#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成绩单上传与解析服务
支持多次上传、版本控制、学号关联
"""
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
from openpyxl import load_workbook

from app.core.logger import get_logger
from app.models.tortoise_models import (
    Student, AcademicScore, AcademicScoreHistory,
    ComprehensiveScore, ComprehensiveScoreHistory,
    UploadRecord, File
)

logger = get_logger(__name__)


class ScoreUploadService:
    """成绩单上传与解析服务"""
    
    FIELD_MAPPING = {
        '学号': 'student_id',
        '姓名': 'student_name',
        '班级': 'class_name',
        '专业名称': 'major',
        '年级': 'grade',
        '总分': 'total_score',
        '门数': 'course_count',
        '总学分': 'total_credits',
        '获得学分': 'earned_credits',
        '算术平均分': 'arithmetic_average',
        '算术平均分排名': 'arithmetic_average_rank',
        '学分加权平均分': 'weighted_average',
        '学分加权平均分排名': 'weighted_average_rank',
        '平均学分绩点': 'average_gpa',
        '平均学分绩点排名': 'average_gpa_rank',
        '不及格门次': 'failed_course_count'
    }
    
    def __init__(self):
        self.upload_dir = Path("uploads/score_sheets")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("成绩单上传服务初始化完成")
    
    def _log_data_trace(self, step: str, data: Any):
        """数据追踪日志"""
        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, ensure_ascii=False, indent=2)
                if len(data_str) > 1000:
                    data_str = data_str[:1000] + "..."
            except Exception:
                data_str = str(data)[:1000]
        else:
            data_str = str(data)[:1000]
        
        logger.info(f"[成绩上传-{step}]\n{data_str}")
    
    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
        academic_year: str,
        semester: str,
        uploaded_by: str,
        upload_role: str = "student"
    ) -> Dict[str, Any]:
        """
        处理成绩单上传
        
        Args:
            file_content: 文件内容
            filename: 文件名
            academic_year: 学年
            semester: 学期
            uploaded_by: 上传者
            upload_role: 上传者角色
            
        Returns:
            处理结果
        """
        self._log_data_trace("开始处理上传", {
            "filename": filename,
            "academic_year": academic_year,
            "semester": semester,
            "uploaded_by": uploaded_by
        })
        
        file_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{file_id}_{filename}"
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        upload_record = await UploadRecord.create(
            file_id=file_id,
            file_name=filename,
            file_type="score_sheet",
            upload_by=uploaded_by,
            upload_role=upload_role,
            academic_year=academic_year,
            semester=semester,
            status="processing"
        )
        
        try:
            df = pd.read_excel(file_path, sheet_name=0, header=0)
            self._log_data_trace("Excel数据读取", {
                "columns": list(df.columns),
                "row_count": len(df)
            })
            
            df = self._normalize_columns(df)
            
            processed = 0
            failed = 0
            results = []
            
            for idx, row in df.iterrows():
                try:
                    result = await self._process_student_row(
                        row, academic_year, semester, filename, uploaded_by
                    )
                    if result['success']:
                        processed += 1
                    else:
                        failed += 1
                    results.append(result)
                except Exception as e:
                    failed += 1
                    logger.error(f"处理第{idx+1}行失败: {e}")
                    results.append({
                        'success': False,
                        'row': idx + 1,
                        'error': str(e)
                    })
            
            upload_record.status = "completed"
            upload_record.processed_count = processed
            upload_record.failed_count = failed
            upload_record.processed_at = datetime.now()
            upload_record.processing_log = json.dumps(results, ensure_ascii=False)
            await upload_record.save()
            
            await File.create(
                id=file_id,
                filename=filename,
                file_path=str(file_path),
                file_size=len(file_content),
                file_type="score_sheet"
            )
            
            self._log_data_trace("处理完成", {
                "processed": processed,
                "failed": failed
            })
            
            return {
                'success': True,
                'file_id': file_id,
                'upload_id': upload_record.id,
                'processed': processed,
                'failed': failed,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"处理成绩单失败: {e}", exc_info=True)
            
            upload_record.status = "failed"
            upload_record.error_message = str(e)
            upload_record.processed_at = datetime.now()
            await upload_record.save()
            
            return {
                'success': False,
                'error': str(e),
                'file_id': file_id
            }
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """规范化列名"""
        df.columns = [str(col).strip() for col in df.columns]
        return df
    
    async def _process_student_row(
        self,
        row: pd.Series,
        academic_year: str,
        semester: str,
        source_file: str,
        changed_by: str
    ) -> Dict[str, Any]:
        """处理单个学生数据行"""
        student_id = str(row.get('student_id', '')).replace('.0', '')
        student_name = str(row.get('student_name', ''))
        
        if not student_id or not student_name:
            return {
                'success': False,
                'student_id': student_id,
                'error': '学号或姓名为空'
            }
        
        self._log_data_trace(f"处理学生 {student_id}", {
            "student_name": student_name,
            "academic_year": academic_year,
            "semester": semester
        })
        
        student = await self._update_or_create_student(row, student_id, student_name)
        
        academic_score = await self._update_or_create_academic_score(
            row, student_id, student_name, academic_year, semester
        )
        
        await self._create_academic_score_history(
            academic_score, source_file, changed_by
        )
        
        return {
            'success': True,
            'student_id': student_id,
            'student_name': student_name,
            'academic_score_id': academic_score.id
        }
    
    async def _update_or_create_student(
        self,
        row: pd.Series,
        student_id: str,
        student_name: str
    ) -> Student:
        """更新或创建学生记录"""
        student = await Student.get_or_none(id=student_id)
        
        class_name = str(row.get('class_name', '')).replace('.0', '')
        major = str(row.get('major', ''))
        grade = str(row.get('grade', '')).replace('.0', '')
        
        if student:
            student.name = student_name
            student.class_name = class_name or student.class_name
            student.major = major or student.major
            student.grade = grade or student.grade
            await student.save()
            self._log_data_trace(f"更新学生 {student_id}", "已存在，更新信息")
        else:
            student = await Student.create(
                id=student_id,
                name=student_name,
                college="计算机学院",
                major=major,
                class_name=class_name,
                grade=grade
            )
            self._log_data_trace(f"创建学生 {student_id}", "新学生")
        
        return student
    
    async def _update_or_create_academic_score(
        self,
        row: pd.Series,
        student_id: str,
        student_name: str,
        academic_year: str,
        semester: str
    ) -> AcademicScore:
        """更新或创建学业成绩记录"""
        
        def safe_float(val, default=0.0):
            try:
                if pd.isna(val):
                    return default
                return float(val)
            except (ValueError, TypeError):
                return default
        
        def safe_int(val, default=None):
            try:
                if pd.isna(val):
                    return default
                return int(float(val))
            except (ValueError, TypeError):
                return default
        
        academic_score = await AcademicScore.get_or_none(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester
        )
        
        score_data = {
            'student_name': student_name,
            'total_score': safe_float(row.get('total_score')),
            'course_count': safe_int(row.get('course_count'), 0),
            'total_credits': safe_float(row.get('total_credits')),
            'earned_credits': safe_float(row.get('earned_credits')),
            'arithmetic_average': safe_float(row.get('arithmetic_average')),
            'arithmetic_average_rank': safe_int(row.get('arithmetic_average_rank')),
            'weighted_average': safe_float(row.get('weighted_average')),
            'weighted_average_rank': safe_int(row.get('weighted_average_rank')),
            'average_gpa': safe_float(row.get('average_gpa')),
            'average_gpa_rank': safe_int(row.get('average_gpa_rank')),
            'failed_course_count': safe_int(row.get('failed_course_count'), 0),
        }
        
        if academic_score:
            for key, value in score_data.items():
                setattr(academic_score, key, value)
            await academic_score.save()
            self._log_data_trace(f"更新学业成绩 {student_id}", score_data)
        else:
            academic_score = await AcademicScore.create(
                student_id=student_id,
                academic_year=academic_year,
                semester=semester,
                **score_data
            )
            self._log_data_trace(f"创建学业成绩 {student_id}", score_data)
        
        return academic_score
    
    async def _create_academic_score_history(
        self,
        academic_score: AcademicScore,
        source_file: str,
        changed_by: str
    ) -> AcademicScoreHistory:
        """创建学业成绩历史记录"""
        last_version = await AcademicScoreHistory.filter(
            academic_score_id=academic_score.id
        ).order_by('-version').first()
        
        version = (last_version.version + 1) if last_version else 1
        
        history = await AcademicScoreHistory.create(
            academic_score_id=academic_score.id,
            student_id=academic_score.student_id,
            version=version,
            total_score=academic_score.total_score,
            course_count=academic_score.course_count,
            total_credits=academic_score.total_credits,
            earned_credits=academic_score.earned_credits,
            arithmetic_average=academic_score.arithmetic_average,
            weighted_average=academic_score.weighted_average,
            average_gpa=academic_score.average_gpa,
            average_credit_gpa=academic_score.average_credit_gpa,
            failed_course_count=academic_score.failed_course_count,
            semester=academic_score.semester,
            academic_year=academic_score.academic_year,
            source_file=source_file,
            change_type="update" if version > 1 else "create",
            changed_by=changed_by
        )
        
        self._log_data_trace(f"创建历史记录 v{version}", {
            "academic_score_id": academic_score.id,
            "version": version
        })
        
        return history
    
    async def get_student_score_history(
        self,
        student_id: str,
        academic_year: str = None,
        semester: str = None
    ) -> List[Dict[str, Any]]:
        """获取学生成绩历史记录"""
        query = AcademicScoreHistory.filter(student_id=student_id)
        
        if academic_year:
            query = query.filter(academic_year=academic_year)
        if semester:
            query = query.filter(semester=semester)
        
        histories = await query.order_by('-created_at').all()
        
        return [{
            'id': h.id,
            'version': h.version,
            'academic_year': h.academic_year,
            'semester': h.semester,
            'weighted_average': h.weighted_average,
            'average_gpa': h.average_gpa,
            'change_type': h.change_type,
            'source_file': h.source_file,
            'changed_by': h.changed_by,
            'created_at': h.created_at.isoformat() if h.created_at else None
        } for h in histories]
    
    async def get_upload_records(
        self,
        upload_by: str = None,
        status: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取上传记录列表"""
        query = UploadRecord.all()
        
        if upload_by:
            query = query.filter(upload_by=upload_by)
        if status:
            query = query.filter(status=status)
        
        records = await query.order_by('-created_at').limit(limit).all()
        
        return [{
            'id': r.id,
            'file_id': r.file_id,
            'file_name': r.file_name,
            'file_type': r.file_type,
            'upload_by': r.upload_by,
            'academic_year': r.academic_year,
            'semester': r.semester,
            'status': r.status,
            'processed_count': r.processed_count,
            'failed_count': r.failed_count,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'processed_at': r.processed_at.isoformat() if r.processed_at else None
        } for r in records]


score_upload_service = ScoreUploadService()


def get_score_upload_service() -> ScoreUploadService:
    """获取成绩上传服务实例"""
    return score_upload_service
