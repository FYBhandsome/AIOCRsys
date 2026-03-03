#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测计算表格解析服务

提供综合测评计算表格的解析和导入功能。
支持动态列标题识别、数据验证和错误报告。
"""

import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from app.core.logger import get_logger
from app.core.exceptions import ExcelParseError, DataValidationError, FileValidationError
from app.core.error_codes import ErrorCode
from app.core.error_response import ErrorDetail

logger = get_logger(__name__)


COMPREHENSIVE_COLUMN_VARIANTS = {
    'rank': ['总排名', '排名', '班级排名', 'rank'],
    'major': ['专业', '专业名称', 'major'],
    'class_name': ['班级', '班级名称', 'class', 'class_name'],
    'student_name': ['姓名', '学生姓名', 'name', 'student_name'],
    'student_id': ['学号', '学生学号', 'student_id', 'id'],
    
    'a1_base_score': ['A1—基础分', 'A1基础分', 'A1-基础分', 'A1', '思想道德基础分', 'a1_score'],
    'a2_bonus_score': ['A2—附加分', 'A2附加分', 'A2-附加分', 'A2', '思想道德附加分', 'a2_score'],
    'a3_deduction': ['A3—扣分项', 'A3扣分项', 'A3-扣分项', 'A3', '思想道德扣分', 'A3—扣罚分', 'a3_score'],
    'a_total': ['思想道德素质(A)总分', 'A总分', '思想道德总分', 'A类总分', 'a_total_score'],
    'a_weighted': ['思想道德素质(A)总分%', 'A总分%', '思想道德加权分', 'A类加权分', '思想道德素质(A)总分20%', 'a_weighted_score'],
    
    'b_raw_score': ['学习成绩', 'B成绩', '学业成绩', 'B类成绩', 'b_total_score'],
    'b_percentage': ['学习成绩%', 'B成绩%', '学业成绩百分比'],
    'b_weighted': ['学习成绩70%', 'B加权分', '学业成绩加权分', 'B类加权分', 'b_weighted_score'],
    
    'c1_tech': ['C1—科技竞赛项目', 'C1科技竞赛', 'C1-科技竞赛项目', 'C1', '科技竞赛加分', 'C1—科技类竞赛项目', 'c1_score'],
    'c2_sports': ['C2—体育竞技项目', 'C2体育竞技', 'C2-体育竞技项目', 'C2', '体育竞技加分', 'c2_score'],
    'c3_culture': ['C3—文化类竞赛项目', 'C3文化竞赛', 'C3-文化类竞赛项目', 'C3', '文化竞赛加分', 'c3_score'],
    'c4_innovation': ['C4—创新创业实践项目', 'C4创新创业', 'C4-创新创业实践项目', 'C4', '创新创业加分', 'c4_score'],
    'c_total': ['素质拓展(C)总分', 'C总分', '素质拓展总分', 'C类总分', '素质拓展（C）总分', 'c_total_score'],
    'c_weighted': ['素质拓展(C)总分10%', 'C加权分', '素质拓展加权分', 'C类加权分', '素质拓展（C）总分10%', 'c_weighted_score'],
    
    'final_score': ['综合测评总成绩8%', '综测总分', '综合测评成绩', '综合测评总成绩', 'total_score'],
    
    'signature': ['学生签字', '签字', 'signature'],
}

COLUMN_DESCRIPTIONS = {
    'rank': '班级排名',
    'major': '专业名称',
    'class_name': '班级名称',
    'student_name': '学生姓名',
    'student_id': '学生学号',
    'a1_base_score': 'A1—基础分（思想道德基础分）',
    'a2_bonus_score': 'A2—附加分（思想道德附加分）',
    'a3_deduction': 'A3—扣分项（思想道德扣分）',
    'a_total': '思想道德素质(A)总分',
    'a_weighted': '思想道德素质(A)加权分(20%)',
    'b_raw_score': '学习成绩（B类原始分）',
    'b_percentage': '学习成绩百分比',
    'b_weighted': '学习成绩加权分(70%)',
    'c1_tech': 'C1—科技竞赛项目加分',
    'c2_sports': 'C2—体育竞技项目加分',
    'c3_culture': 'C3—文化类竞赛项目加分',
    'c4_innovation': 'C4—创新创业实践项目加分',
    'c_total': '素质拓展(C)总分',
    'c_weighted': '素质拓展(C)加权分(10%)',
    'final_score': '综合测评总成绩',
    'signature': '学生签字',
}


@dataclass
class ComprehensiveParseResult:
    """综测表格解析结果"""
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    total_rows: int = 0
    parsed_rows: int = 0
    skipped_rows: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    column_mapping: Dict[str, int] = field(default_factory=dict)
    missing_columns: List[str] = field(default_factory=list)
    recognized_columns: List[str] = field(default_factory=list)
    sheet_name: Optional[str] = None
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'success': self.success,
            'data': self.data,
            'total_rows': self.total_rows,
            'parsed_rows': self.parsed_rows,
            'skipped_rows': self.skipped_rows,
            'errors': self.errors,
            'warnings': self.warnings,
            'column_mapping': self.column_mapping,
            'missing_columns': self.missing_columns,
            'recognized_columns': self.recognized_columns,
            'sheet_name': self.sheet_name,
            'file_path': self.file_path,
        }


@dataclass
class ColumnMatchResult:
    """列匹配结果"""
    column_mapping: Dict[str, int]
    recognized_columns: List[str]
    missing_columns: List[str]
    warnings: List[str]
    confidence: float = 0.0


class ComprehensiveTableParser:
    """综测计算表格解析器"""
    
    REQUIRED_COLUMNS = ['student_id', 'student_name']
    RECOMMENDED_COLUMNS = ['class_name', 'final_score']
    NUMERIC_COLUMNS = [
        'rank', 'a1_base_score', 'a2_bonus_score', 'a3_deduction',
        'a_total', 'a_weighted', 'b_raw_score', 'b_percentage',
        'b_weighted', 'c1_tech', 'c2_sports', 'c3_culture',
        'c4_innovation', 'c_total', 'c_weighted', 'final_score'
    ]
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def parse_excel_file(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        header_row: int = 2,
        skip_empty_rows: bool = True
    ) -> ComprehensiveParseResult:
        """
        解析综测计算表格Excel文件
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称，默认自动检测
            header_row: 标题行位置（从0开始）
            skip_empty_rows: 是否跳过空行
            
        Returns:
            ComprehensiveParseResult 解析结果
        """
        self.logger.info(f"开始解析综测计算表格: {file_path}")
        
        result = ComprehensiveParseResult(
            success=False,
            file_path=file_path
        )
        
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileValidationError(
                    error_code=ErrorCode.FILE_NOT_FOUND,
                    message=f"文件不存在: {file_path}",
                    filename=file_path
                )
            
            if path.suffix.lower() not in ['.xlsx', '.xls']:
                raise FileValidationError(
                    error_code=ErrorCode.FILE_INVALID_FORMAT,
                    message="文件格式不支持，请使用 .xlsx 或 .xls 格式",
                    filename=file_path
                )
            
            xl = pd.ExcelFile(file_path)
            
            if sheet_name:
                if sheet_name not in xl.sheet_names:
                    result.errors.append({
                        'code': ErrorCode.EXCEL_SHEET_NOT_FOUND,
                        'message': f"工作表 '{sheet_name}' 不存在",
                        'available_sheets': xl.sheet_names
                    })
                    return result
            else:
                sheet_name = self._detect_comprehensive_sheet(xl.sheet_names)
                if not sheet_name:
                    sheet_name = xl.sheet_names[0]
                    result.warnings.append(f"未找到综测计算表，使用第一个工作表: {sheet_name}")
            
            result.sheet_name = sheet_name
            
            df = pd.read_excel(xl, sheet_name=sheet_name, header=header_row)
            
            if df.empty:
                result.errors.append({
                    'code': ErrorCode.EXCEL_EMPTY_SHEET,
                    'message': f"工作表 '{sheet_name}' 为空"
                })
                return result
            
            self.logger.info(f"读取到 {len(df)} 行数据，列数: {len(df.columns)}")
            
            match_result = self._identify_columns(df)
            result.column_mapping = match_result.column_mapping
            result.recognized_columns = match_result.recognized_columns
            result.missing_columns = match_result.missing_columns
            result.warnings.extend(match_result.warnings)
            
            if match_result.missing_columns:
                missing_required = [c for c in match_result.missing_columns if c in self.REQUIRED_COLUMNS]
                if missing_required:
                    result.errors.append({
                        'code': ErrorCode.EXCEL_MISSING_COLUMNS,
                        'message': f"缺少必要的列: {', '.join([COLUMN_DESCRIPTIONS.get(c, c) for c in missing_required])}",
                        'missing_columns': missing_required
                    })
                    return result
            
            result.total_rows = len(df)
            
            for idx, row in df.iterrows():
                try:
                    parsed_row = self._parse_row(row, match_result.column_mapping, idx + header_row + 1)
                    if parsed_row:
                        validation_result = self.validate_comprehensive_data(parsed_row)
                        if validation_result['valid']:
                            result.data.append(parsed_row)
                            result.parsed_rows += 1
                        else:
                            result.skipped_rows += 1
                            result.errors.append({
                                'code': ErrorCode.DATA_INVALID_FORMAT,
                                'message': validation_result['message'],
                                'row': idx + header_row + 1,
                                'data': parsed_row
                            })
                    else:
                        if skip_empty_rows:
                            result.skipped_rows += 1
                except Exception as e:
                    result.skipped_rows += 1
                    self.logger.error(f"解析第 {idx + header_row + 1} 行失败: {e}")
                    result.errors.append({
                        'code': ErrorCode.EXCEL_INVALID_DATA,
                        'message': str(e),
                        'row': idx + header_row + 1
                    })
            
            result.success = result.parsed_rows > 0
            
            self.logger.info(
                f"解析完成: 成功 {result.parsed_rows} 行, "
                f"跳过 {result.skipped_rows} 行, "
                f"错误 {len(result.errors)} 条"
            )
            
            return result
            
        except FileValidationError:
            raise
        except pd.errors.EmptyDataError:
            result.errors.append({
                'code': ErrorCode.FILE_EMPTY,
                'message': "文件内容为空"
            })
            return result
        except Exception as e:
            self.logger.error(f"解析文件失败: {e}", exc_info=True)
            result.errors.append({
                'code': ErrorCode.FILE_PARSE_ERROR,
                'message': f"解析文件失败: {str(e)}"
            })
            return result
    
    def _detect_comprehensive_sheet(self, sheet_names: List[str]) -> Optional[str]:
        """检测综测计算表工作表"""
        keywords = ['综合测评', '综测', '计算表', 'comprehensive']
        
        for name in sheet_names:
            for keyword in keywords:
                if keyword in name.lower():
                    return name
        
        return None
    
    def _identify_columns(self, df: pd.DataFrame) -> ColumnMatchResult:
        """
        识别列标题
        
        使用模糊匹配算法识别Excel列标题与标准字段的对应关系
        """
        column_mapping = {}
        recognized_columns = []
        missing_columns = []
        warnings = []
        
        df_columns = [str(col).strip() for col in df.columns]
        
        for field_name, variants in COMPREHENSIVE_COLUMN_VARIANTS.items():
            matched = False
            best_match_idx = -1
            best_match_score = 0
            
            for idx, col_name in enumerate(df_columns):
                if idx in column_mapping.values():
                    continue
                
                col_lower = col_name.lower().replace(' ', '').replace('—', '-').replace('（', '(').replace('）', ')')
                
                for variant in variants:
                    variant_lower = variant.lower().replace(' ', '').replace('—', '-').replace('（', '(').replace('）', ')')
                    
                    if col_lower == variant_lower:
                        column_mapping[field_name] = idx
                        recognized_columns.append(field_name)
                        matched = True
                        best_match_idx = idx
                        break
                    
                    if variant_lower in col_lower or col_lower in variant_lower:
                        score = len(variant_lower) / max(len(col_lower), len(variant_lower))
                        if score > best_match_score and score > 0.5:
                            best_match_score = score
                            best_match_idx = idx
            
                if matched:
                    break
            
            if not matched and best_match_idx >= 0:
                column_mapping[field_name] = best_match_idx
                recognized_columns.append(field_name)
                warnings.append(f"列 '{df_columns[best_match_idx]}' 被识别为 '{COLUMN_DESCRIPTIONS.get(field_name, field_name)}'")
        
        for req_col in self.REQUIRED_COLUMNS:
            if req_col not in column_mapping:
                missing_columns.append(req_col)
        
        for rec_col in self.RECOMMENDED_COLUMNS:
            if rec_col not in column_mapping:
                warnings.append(f"建议添加列: {COLUMN_DESCRIPTIONS.get(rec_col, rec_col)}")
        
        confidence = len(recognized_columns) / len(COMPREHENSIVE_COLUMN_VARIANTS) if COMPREHENSIVE_COLUMN_VARIANTS else 0
        
        return ColumnMatchResult(
            column_mapping=column_mapping,
            recognized_columns=recognized_columns,
            missing_columns=missing_columns,
            warnings=warnings,
            confidence=confidence
        )
    
    def _parse_row(
        self,
        row: pd.Series,
        column_mapping: Dict[str, int],
        row_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        解析单行数据
        
        Args:
            row: pandas Series 行数据
            column_mapping: 列映射
            row_index: 行号
            
        Returns:
            解析后的数据字典，如果行为空则返回 None
        """
        data = {
            'row_index': row_index,
            'raw_data': {}
        }
        
        for field_name, col_idx in column_mapping.items():
            if col_idx < len(row):
                value = row.iloc[col_idx]
                data['raw_data'][field_name] = value
                
                if field_name in self.NUMERIC_COLUMNS:
                    data[field_name] = self._parse_numeric(value)
                else:
                    data[field_name] = self._parse_string(value)
        
        student_id = data.get('student_id')
        student_name = data.get('student_name')
        
        if not student_id and not student_name:
            return None
        
        if student_id:
            data['student_id'] = str(student_id).replace('.0', '').strip()
        
        return data
    
    def _parse_numeric(self, value: Any) -> Optional[float]:
        """解析数值"""
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        try:
            cleaned = str(value).strip()
            cleaned = re.sub(r'[^\d.\-+]', '', cleaned)
            if cleaned:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _parse_string(self, value: Any) -> Optional[str]:
        """解析字符串"""
        if pd.isna(value):
            return None
        
        result = str(value).strip()
        
        if result.endswith('.0'):
            result = result[:-2]
        
        return result
    
    def validate_comprehensive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证综测数据
        
        Args:
            data: 待验证的数据字典
            
        Returns:
            验证结果，包含 valid, message, errors 字段
        """
        errors = []
        
        student_id = data.get('student_id')
        if not student_id:
            errors.append({
                'field': 'student_id',
                'message': '学号不能为空'
            })
        elif not self._validate_student_id(student_id):
            errors.append({
                'field': 'student_id',
                'message': f'学号格式无效: {student_id}'
            })
        
        student_name = data.get('student_name')
        if not student_name:
            errors.append({
                'field': 'student_name',
                'message': '姓名不能为空'
            })
        
        score_fields = {
            'a1_base_score': (0, 100, 'A1基础分'),
            'a2_bonus_score': (0, 50, 'A2附加分'),
            'a3_deduction': (0, 50, 'A3扣分项'),
            'b_raw_score': (0, 100, '学习成绩'),
            'final_score': (0, 100, '综合测评总成绩'),
        }
        
        for field, (min_val, max_val, desc) in score_fields.items():
            value = data.get(field)
            if value is not None:
                if not isinstance(value, (int, float)):
                    errors.append({
                        'field': field,
                        'message': f'{desc}必须是数值'
                    })
                elif value < min_val or value > max_val:
                    errors.append({
                        'field': field,
                        'message': f'{desc}应在 {min_val}-{max_val} 范围内，当前值: {value}'
                    })
        
        a1 = data.get('a1_base_score') or 0
        a2 = data.get('a2_bonus_score') or 0
        a3 = data.get('a3_deduction') or 0
        a_total = data.get('a_total')
        
        if a_total is not None:
            expected_a_total = a1 + a2 + a3
            if abs(a_total - expected_a_total) > 0.1:
                data['a_total_mismatch'] = {
                    'expected': expected_a_total,
                    'actual': a_total
                }
        
        c1 = data.get('c1_tech') or 0
        c2 = data.get('c2_sports') or 0
        c3 = data.get('c3_culture') or 0
        c4 = data.get('c4_innovation') or 0
        c_total = data.get('c_total')
        
        if c_total is not None:
            expected_c_total = c1 + c2 + c3 + c4
            if abs(c_total - expected_c_total) > 0.1:
                data['c_total_mismatch'] = {
                    'expected': expected_c_total,
                    'actual': c_total
                }
        
        if errors:
            return {
                'valid': False,
                'message': '; '.join([e['message'] for e in errors]),
                'errors': errors
            }
        
        return {
            'valid': True,
            'message': '验证通过'
        }
    
    def _validate_student_id(self, student_id: str) -> bool:
        """验证学号格式"""
        if not student_id:
            return False
        
        student_id = str(student_id).strip()
        
        if len(student_id) < 6 or len(student_id) > 20:
            return False
        
        if not re.match(r'^[A-Za-z0-9]+$', student_id):
            return False
        
        return True
    
    def get_column_template(self) -> Dict[str, Any]:
        """获取标准列模板"""
        return {
            'columns': [
                {
                    'field': field,
                    'description': COLUMN_DESCRIPTIONS.get(field, field),
                    'variants': variants,
                    'required': field in self.REQUIRED_COLUMNS,
                    'recommended': field in self.RECOMMENDED_COLUMNS,
                    'numeric': field in self.NUMERIC_COLUMNS
                }
                for field, variants in COMPREHENSIVE_COLUMN_VARIANTS.items()
            ],
            'required_columns': self.REQUIRED_COLUMNS,
            'recommended_columns': self.RECOMMENDED_COLUMNS,
            'numeric_columns': self.NUMERIC_COLUMNS
        }


class ComprehensiveScoreImportService:
    """综测计算表格导入服务"""
    
    def __init__(self):
        self.parser = ComprehensiveTableParser()
        self.logger = get_logger(__name__)
    
    async def import_from_excel(
        self,
        file_path: str,
        academic_year: str,
        semester: str,
        class_id: Optional[str] = None,
        create_student: bool = True,
        update_existing: bool = True
    ) -> Dict[str, Any]:
        """
        从Excel文件导入综测数据到数据库
        
        Args:
            file_path: Excel文件路径
            academic_year: 学年
            semester: 学期
            class_id: 班级ID
            create_student: 是否自动创建学生
            update_existing: 是否更新已存在的记录
            
        Returns:
            导入结果
        """
        from app.models.tortoise_models import Student, Class, ComprehensiveScore
        
        self.logger.info(f"开始导入综测数据: {file_path}")
        
        parse_result = self.parser.parse_excel_file(file_path)
        
        if not parse_result.success:
            return {
                'success': False,
                'message': '解析文件失败',
                'parse_result': parse_result.to_dict()
            }
        
        import_stats = {
            'total_rows': parse_result.total_rows,
            'parsed_rows': parse_result.parsed_rows,
            'students_created': 0,
            'students_updated': 0,
            'scores_created': 0,
            'scores_updated': 0,
            'errors': []
        }
        
        for data in parse_result.data:
            try:
                student_id = data.get('student_id')
                student_name = data.get('student_name')
                
                if not student_id:
                    continue
                
                student = await Student.get_or_none(id=student_id)
                
                if student:
                    if update_existing:
                        student.name = student_name or student.name
                        if data.get('class_name'):
                            student.class_name = data['class_name']
                        if data.get('major'):
                            student.major = data['major']
                        if data.get('final_score') is not None:
                            student.total_score = data['final_score']
                        await student.save()
                        import_stats['students_updated'] += 1
                elif create_student:
                    student = await Student.create(
                        id=student_id,
                        name=student_name or '',
                        college='计算机学院',
                        major=data.get('major', ''),
                        class_name=data.get('class_name', class_id or ''),
                        grade=f"20{student_id[:2]}" if len(student_id) >= 2 else '',
                        total_score=data.get('final_score', 0) or 0
                    )
                    import_stats['students_created'] += 1
                
                score_data = {
                    'student_id': student_id,
                    'student_name': student_name,
                    'class_name': data.get('class_name', class_id),
                    'major': data.get('major'),
                    'semester': semester,
                    'academic_year': academic_year,
                    'a1_score': data.get('a1_base_score') or 0,
                    'a2_score': data.get('a2_bonus_score') or 0,
                    'a3_score': data.get('a3_deduction') or 0,
                    'a_total_score': data.get('a_total') or 0,
                    'a_weighted_score': data.get('a_weighted') or 0,
                    'b_total_score': data.get('b_raw_score') or 0,
                    'b_weighted_score': data.get('b_weighted') or 0,
                    'c1_score': data.get('c1_tech') or 0,
                    'c2_score': data.get('c2_sports') or 0,
                    'c3_score': data.get('c3_culture') or 0,
                    'c4_score': data.get('c4_innovation') or 0,
                    'c_total_score': data.get('c_total') or 0,
                    'c_weighted_score': data.get('c_weighted') or 0,
                    'total_score': data.get('final_score') or 0,
                    'ranking': int(data.get('rank')) if data.get('rank') else None,
                    'source_file': file_path,
                    'source_type': 'comprehensive_table'
                }
                
                existing_score = await ComprehensiveScore.get_or_none(
                    student_id=student_id,
                    semester=semester,
                    academic_year=academic_year
                )
                
                if existing_score:
                    if update_existing:
                        for key, value in score_data.items():
                            if key not in ['student_id', 'semester', 'academic_year']:
                                setattr(existing_score, key, value)
                        await existing_score.save()
                        import_stats['scores_updated'] += 1
                else:
                    await ComprehensiveScore.create(**score_data)
                    import_stats['scores_created'] += 1
                    
            except Exception as e:
                self.logger.error(f"导入学生 {data.get('student_id')} 数据失败: {e}")
                import_stats['errors'].append({
                    'student_id': data.get('student_id'),
                    'error': str(e)
                })
        
        self.logger.info(f"导入完成: {import_stats}")
        
        return {
            'success': True,
            'message': f"导入完成：创建学生{import_stats['students_created']}人，"
                      f"更新学生{import_stats['students_updated']}人，"
                      f"创建成绩{import_stats['scores_created']}条，"
                      f"更新成绩{import_stats['scores_updated']}条",
            'stats': import_stats,
            'parse_result': parse_result.to_dict()
        }
    
    async def preview_import(
        self,
        file_path: str,
        max_rows: int = 10
    ) -> Dict[str, Any]:
        """
        预览导入数据
        
        Args:
            file_path: Excel文件路径
            max_rows: 最大预览行数
            
        Returns:
            预览结果
        """
        parse_result = self.parser.parse_excel_file(file_path)
        
        preview_data = parse_result.data[:max_rows]
        
        return {
            'success': parse_result.success,
            'total_rows': parse_result.total_rows,
            'parsed_rows': parse_result.parsed_rows,
            'column_mapping': parse_result.column_mapping,
            'recognized_columns': parse_result.recognized_columns,
            'missing_columns': parse_result.missing_columns,
            'warnings': parse_result.warnings,
            'errors': parse_result.errors,
            'preview_data': preview_data,
            'template': self.parser.get_column_template()
        }


_comprehensive_table_parser_instance: Optional[ComprehensiveTableParser] = None
_comprehensive_score_import_service_instance: Optional[ComprehensiveScoreImportService] = None


def get_comprehensive_table_parser() -> ComprehensiveTableParser:
    """获取综测计算表格解析器单例"""
    global _comprehensive_table_parser_instance
    if _comprehensive_table_parser_instance is None:
        _comprehensive_table_parser_instance = ComprehensiveTableParser()
    return _comprehensive_table_parser_instance


def get_comprehensive_score_import_service() -> ComprehensiveScoreImportService:
    """获取综测计算表格导入服务单例"""
    global _comprehensive_score_import_service_instance
    if _comprehensive_score_import_service_instance is None:
        _comprehensive_score_import_service_instance = ComprehensiveScoreImportService()
    return _comprehensive_score_import_service_instance
