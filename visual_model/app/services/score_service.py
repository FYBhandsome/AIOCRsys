#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成绩导入服务

提供Excel成绩文件的解析和导入功能。
支持动态列标题识别和固定索引两种解析方式。
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field

from app.core.logger import logger
from app.core.exceptions import FileUploadException
from app.core.error_codes import ErrorCode, ERROR_MESSAGES, ERROR_SUGGESTIONS
from app.core.error_response import ErrorDetail, create_error_response


# 标准列标题映射表（支持多种命名变体）
COLUMN_VARIANTS: Dict[str, List[str]] = {
    "学号": ["学号", "学生学号", "student_id", "学号\n", "学生编号", "studentid", "id"],
    "姓名": ["姓名", "学生姓名", "name", "学生名称", "学生", "student_name"],
    "班级": ["班级", "班级名称", "class_name", "class", "班级名", "行政班"],
    "专业": ["专业", "专业名称", "major", "专业名", "所属专业"],
    "年级": ["年级", "grade", "入学年级", "学生年级"],
    "学院": ["学院", "学院名称", "college", "院系", "所属学院", "系别"],
    "总分": ["总分", "总成绩", "total_score", "成绩总分", "分数"],
    "总应获得学分": ["总应获得学分", "应得学分", "required_credits", "总应得学分"],
    "门数": ["门数", "课程门数", "course_count", "总门数", "选课门数"],
    "总学分": ["总学分", "total_credits", "学分总计"],
    "获得学分": ["获得学分", "已获学分", "earned_credits", "取得学分"],
    "不及格学分": ["不及格学分", "挂科学分", "failed_credits", "未通过学分"],
    "通过率": ["通过率", "及格率", "pass_rate", "合格率"],
    "算术平均分": ["算术平均分", "平均分", "arithmetic_average", "avg", "平均成绩", "算术平均"],
    "算术平均分排名": ["算术平均分排名", "平均分排名", "arithmetic_average_rank", "平均分名次"],
    "学分加权平均分": ["学分加权平均分", "加权平均分", "weighted_average", "加权平均", "加权成绩"],
    "学分加权平均分排名": ["学分加权平均分排名", "加权平均分排名", "weighted_average_rank", "加权排名"],
    "平均绩点": ["平均绩点", "平均GPA", "average_gpa", "GPA", "绩点", "avg_gpa"],
    "平均绩点排名": ["平均绩点排名", "GPA排名", "average_gpa_rank", "绩点排名"],
    "平均学分绩点": ["平均学分绩点", "学分绩点", "average_credit_gpa", "平均学分绩"],
    "平均学分绩点排名": ["平均学分绩点排名", "学分绩点排名", "average_credit_gpa_rank"],
    "学分绩点和": ["学分绩点和", "绩点和", "credit_gpa_sum", "学分绩点总和"],
    "学分绩点和排名": ["学分绩点和排名", "绩点和排名", "credit_gpa_sum_rank"],
    "不及格门次": ["不及格门次", "挂科门数", "failed_course_count", "不及格门数"],
}

# 必需列列表（用于验证）
REQUIRED_COLUMNS: List[str] = ["学号", "姓名"]

# 推荐列列表（建议存在但不是必需）
RECOMMENDED_COLUMNS: List[str] = ["班级", "专业", "年级", "总分", "算术平均分"]

# 固定索引映射（向后兼容）
TABLE_MAP: Dict[str, int] = {
    "学号": 0,
    "姓名": 1,
    "总分": 2,
    "总应获得学分": 3,
    "门数": 4,
    "总学分": 5,
    "获得学分": 6,
    "不及格学分": 7,
    "通过率": 8,
    "算术平均分": 9,
    "算术平均分排名": 10,
    "学分加权平均分": 11,
    "学分加权平均分排名": 12,
    "平均绩点": 13,
    "平均绩点排名": 14,
    "平均学分绩点": 15,
    "平均学分绩点排名": 16,
    "学分绩点和": 17,
    "学分绩点和排名": 18,
    "不及格门次": 19,
    "学院": 20,
    "年级": 21,
    "专业": 22,
    "班级": 23
}

# 标准字段名到数据库字段的映射
COLUMN_TO_FIELD_MAP: Dict[str, str] = {
    "学号": "student_id",
    "姓名": "student_name",
    "班级": "class_name",
    "专业": "major",
    "年级": "grade",
    "学院": "college",
    "总分": "total_score",
    "总应获得学分": "total_required_credits",
    "门数": "course_count",
    "总学分": "total_credits",
    "获得学分": "earned_credits",
    "不及格学分": "failed_credits",
    "通过率": "pass_rate",
    "算术平均分": "arithmetic_average",
    "算术平均分排名": "arithmetic_average_rank",
    "学分加权平均分": "weighted_average",
    "学分加权平均分排名": "weighted_average_rank",
    "平均绩点": "average_gpa",
    "平均绩点排名": "average_gpa_rank",
    "平均学分绩点": "average_credit_gpa",
    "平均学分绩点排名": "average_credit_gpa_rank",
    "学分绩点和": "credit_gpa_sum",
    "学分绩点和排名": "credit_gpa_sum_rank",
    "不及格门次": "failed_course_count",
}


@dataclass
class ColumnMappingResult:
    """列映射结果"""
    column_map: Dict[str, str] = field(default_factory=dict)
    unrecognized_columns: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    missing_recommended: List[str] = field(default_factory=list)
    use_index_mode: bool = False
    confidence: float = 0.0


@dataclass
class ParseResult:
    """解析结果"""
    scores: List[Dict[str, Any]] = field(default_factory=list)
    total_rows: int = 0
    success_rows: int = 0
    failed_rows: int = 0
    column_mapping: Optional[ColumnMappingResult] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ExcelStructureValidator:
    """Excel文件结构验证器
    
    负责验证Excel文件的结构是否符合成绩导入的要求，
    包括列标题验证、数据类型检查等功能。
    """
    
    REQUIRED_COLUMNS = ['student_id', 'student_name']
    
    RECOMMENDED_COLUMNS = ['class_name', 'major', 'grade', 'arithmetic_average', 'weighted_average']
    
    FIELD_TYPE_MAP = {
        'student_id': 'string',
        'student_name': 'string',
        'class_name': 'string',
        'major': 'string',
        'grade': 'string',
        'college': 'string',
        'total_score': 'numeric',
        'total_required_credits': 'numeric',
        'course_count': 'integer',
        'total_credits': 'numeric',
        'earned_credits': 'numeric',
        'failed_credits': 'numeric',
        'pass_rate': 'numeric',
        'arithmetic_average': 'numeric',
        'arithmetic_average_rank': 'integer',
        'weighted_average': 'numeric',
        'weighted_average_rank': 'integer',
        'average_gpa': 'numeric',
        'average_gpa_rank': 'integer',
        'average_credit_gpa': 'numeric',
        'average_credit_gpa_rank': 'integer',
        'credit_gpa_sum': 'numeric',
        'credit_gpa_sum_rank': 'integer',
        'failed_course_count': 'integer',
    }
    
    def validate_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """验证Excel结构
        
        检查DataFrame是否包含必需列和推荐列，识别多余列，
        并生成验证报告。
        
        Args:
            df: pandas DataFrame
            
        Returns:
            {
                'valid': bool,  # 是否通过验证
                'missing_required': List[str],  # 缺失的必需列
                'missing_recommended': List[str],  # 缺失的推荐列
                'extra_columns': List[str],  # 多余的列
                'warnings': List[str],  # 警告信息
            }
        """
        result = {
            'valid': True,
            'missing_required': [],
            'missing_recommended': [],
            'extra_columns': [],
            'warnings': []
        }
        
        df_columns = [str(col).lower().strip() for col in df.columns.tolist()]
        all_known_columns = set(self.REQUIRED_COLUMNS + self.RECOMMENDED_COLUMNS + list(self.FIELD_TYPE_MAP.keys()))
        
        for col in self.REQUIRED_COLUMNS:
            col_variants = self._get_column_variants(col)
            found = any(variant.lower() in df_columns for variant in col_variants)
            if not found:
                result['missing_required'].append(col)
                result['valid'] = False
        
        for col in self.RECOMMENDED_COLUMNS:
            col_variants = self._get_column_variants(col)
            found = any(variant.lower() in df_columns for variant in col_variants)
            if not found:
                result['missing_recommended'].append(col)
        
        for df_col in df.columns.tolist():
            normalized_col = str(df_col).lower().strip()
            col_variants = []
            for known_col in all_known_columns:
                col_variants.extend(self._get_column_variants(known_col))
            
            if not any(variant.lower() == normalized_col for variant in col_variants):
                result['extra_columns'].append(str(df_col))
        
        if result['missing_required']:
            result['warnings'].append(f"缺少必需列: {', '.join(result['missing_required'])}")
        
        if result['missing_recommended']:
            result['warnings'].append(f"缺少推荐列: {', '.join(result['missing_recommended'])}")
        
        if result['extra_columns']:
            result['warnings'].append(f"存在未识别的列: {', '.join(result['extra_columns'][:5])}")
        
        logger.info(f"Excel结构验证完成: valid={result['valid']}, missing_required={result['missing_required']}")
        
        return result
    
    def _get_column_variants(self, field_name: str) -> List[str]:
        """获取字段名对应的所有可能的列名变体
        
        Args:
            field_name: 字段名（如 student_id）
            
        Returns:
            列名变体列表
        """
        reverse_map = {}
        for cn_name, en_name in COLUMN_TO_FIELD_MAP.items():
            if en_name not in reverse_map:
                reverse_map[en_name] = []
            reverse_map[en_name].append(cn_name)
        
        variants = [field_name]
        
        if field_name in reverse_map:
            variants.extend(reverse_map[field_name])
        
        if field_name in COLUMN_VARIANTS:
            variants.extend(COLUMN_VARIANTS[field_name])
        
        for cn_name, en_name in COLUMN_TO_FIELD_MAP.items():
            if en_name == field_name:
                variants.append(cn_name)
                if cn_name in COLUMN_VARIANTS:
                    variants.extend(COLUMN_VARIANTS[cn_name])
        
        return list(set(variants))
    
    def check_data_types(self, df: pd.DataFrame, column_mapping: Dict[str, int]) -> Dict[str, Any]:
        """检查数据类型
        
        根据列映射检查DataFrame中各列的数据类型是否符合预期。
        
        Args:
            df: pandas DataFrame
            column_mapping: 列映射字典，键为标准字段名，值为列索引或列名
            
        Returns:
            {
                'valid': bool,  # 是否通过验证
                'type_errors': List[Dict],  # 类型错误列表
            }
        """
        result = {
            'valid': True,
            'type_errors': []
        }
        
        for field_name, expected_type in self.FIELD_TYPE_MAP.items():
            if field_name not in column_mapping:
                continue
            
            col_ref = column_mapping[field_name]
            
            if isinstance(col_ref, int):
                if col_ref >= len(df.columns):
                    continue
                col_data = df.iloc[:, col_ref]
            else:
                if col_ref not in df.columns:
                    continue
                col_data = df[col_ref]
            
            type_errors = self._check_column_type(col_data, field_name, expected_type)
            if type_errors:
                result['type_errors'].extend(type_errors)
                result['valid'] = False
        
        if result['type_errors']:
            logger.warning(f"数据类型检查发现 {len(result['type_errors'])} 个错误")
        
        return result
    
    def _check_column_type(self, col_data: pd.Series, field_name: str, expected_type: str) -> List[Dict[str, Any]]:
        """检查单列的数据类型
        
        Args:
            col_data: 列数据
            field_name: 字段名
            expected_type: 期望类型
            
        Returns:
            类型错误列表
        """
        errors = []
        
        for idx, value in col_data.items():
            if pd.isna(value):
                continue
            
            is_valid = True
            actual_type = type(value).__name__
            
            if expected_type == 'string':
                if not isinstance(value, (str, int, float)):
                    is_valid = False
            elif expected_type == 'numeric':
                if isinstance(value, str):
                    try:
                        float(value.replace('%', '').strip())
                    except (ValueError, AttributeError):
                        is_valid = False
                elif not isinstance(value, (int, float)):
                    is_valid = False
            elif expected_type == 'integer':
                if isinstance(value, str):
                    try:
                        int(float(value.strip()))
                    except (ValueError, AttributeError):
                        is_valid = False
                elif isinstance(value, float) and not value.is_integer():
                    is_valid = False
                elif not isinstance(value, (int, float)):
                    is_valid = False
            
            if not is_valid:
                errors.append({
                    'row': int(idx) + 2,
                    'field': field_name,
                    'expected_type': expected_type,
                    'actual_type': actual_type,
                    'value': str(value)[:50],
                    'error_code': ErrorCode.DATA_INVALID_FORMAT,
                    'message': f"第{int(idx) + 2}行字段'{field_name}'类型错误，期望{expected_type}，实际为{actual_type}"
                })
        
        return errors


class DataValidator:
    """数据校验器
    
    负责验证成绩数据的具体内容，包括学号格式、分数范围、
    必填字段等校验功能。
    """
    
    STUDENT_ID_PATTERN = r'^\d{8,12}$'
    
    SCORE_RANGES = {
        'arithmetic_average': (0, 100),
        'weighted_average': (0, 100),
        'average_gpa': (0, 5),
        'pass_rate': (0, 100),
        'total_score': (0, 500),
        'total_required_credits': (0, 300),
        'total_credits': (0, 300),
        'earned_credits': (0, 300),
        'failed_credits': (0, 300),
        'course_count': (0, 100),
        'failed_course_count': (0, 100),
    }
    
    REQUIRED_FIELDS = ['student_id', 'student_name']
    
    def validate_student_id(self, student_id: str) -> Dict[str, Any]:
        """验证学号格式
        
        检查学号是否符合预期的格式要求（8-12位数字）。
        
        Args:
            student_id: 学号字符串
            
        Returns:
            {
                'valid': bool,  # 是否有效
                'error': Optional[str],  # 错误信息
                'error_code': Optional[int],  # 错误代码
            }
        """
        result = {
            'valid': True,
            'error': None,
            'error_code': None
        }
        
        if not student_id:
            result['valid'] = False
            result['error'] = '学号不能为空'
            result['error_code'] = ErrorCode.DATA_MISSING_REQUIRED
            return result
        
        student_id = str(student_id).strip()
        
        if not re.match(self.STUDENT_ID_PATTERN, student_id):
            result['valid'] = False
            result['error'] = f'学号格式无效，应为8-12位数字，当前值: {student_id}'
            result['error_code'] = ErrorCode.DATA_INVALID_STUDENT_ID
        
        return result
    
    def validate_score_range(self, field: str, value: float) -> Dict[str, Any]:
        """验证分数范围
        
        检查数值字段是否在有效范围内。
        
        Args:
            field: 字段名
            value: 数值
            
        Returns:
            {
                'valid': bool,  # 是否有效
                'error': Optional[str],  # 错误信息
                'error_code': Optional[int],  # 错误代码
                'range': Optional[Tuple],  # 有效范围
            }
        """
        result = {
            'valid': True,
            'error': None,
            'error_code': None,
            'range': None
        }
        
        if field not in self.SCORE_RANGES:
            return result
        
        min_val, max_val = self.SCORE_RANGES[field]
        result['range'] = (min_val, max_val)
        
        try:
            num_value = float(value)
            if num_value < min_val or num_value > max_val:
                result['valid'] = False
                result['error'] = f'{field} 值 {num_value} 超出有效范围 [{min_val}, {max_val}]'
                result['error_code'] = ErrorCode.DATA_OUT_OF_RANGE
        except (ValueError, TypeError):
            result['valid'] = False
            result['error'] = f'{field} 值 "{value}" 不是有效数字'
            result['error_code'] = ErrorCode.DATA_INVALID_FORMAT
        
        return result
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """验证必填字段
        
        检查数据中是否包含所有必填字段且值不为空。
        
        Args:
            data: 数据字典
            required_fields: 必填字段列表
            
        Returns:
            {
                'valid': bool,  # 是否有效
                'missing_fields': List[str],  # 缺失字段列表
                'errors': List[Dict],  # 错误详情列表
            }
        """
        result = {
            'valid': True,
            'missing_fields': [],
            'errors': []
        }
        
        for field in required_fields:
            value = data.get(field)
            
            if value is None or (isinstance(value, str) and not value.strip()):
                result['missing_fields'].append(field)
                result['errors'].append({
                    'field': field,
                    'error': f'必填字段 {field} 缺失或为空',
                    'error_code': ErrorCode.DATA_MISSING_REQUIRED
                })
                result['valid'] = False
        
        return result
    
    def validate_row(self, row_data: Dict[str, Any], row_index: int) -> Dict[str, Any]:
        """验证单行数据
        
        对单行数据进行全面验证，包括必填字段、学号格式、数值范围等。
        
        Args:
            row_data: 行数据字典
            row_index: 行索引（用于错误定位）
            
        Returns:
            {
                'valid': bool,  # 是否有效
                'row_index': int,  # 行索引
                'errors': List[Dict],  # 错误列表
                'warnings': List[str],  # 警告列表
            }
        """
        result = {
            'valid': True,
            'row_index': row_index,
            'errors': [],
            'warnings': []
        }
        
        required_result = self.validate_required_fields(row_data, self.REQUIRED_FIELDS)
        if not required_result['valid']:
            result['valid'] = False
            for error in required_result['errors']:
                result['errors'].append({
                    'row': row_index,
                    'field': error['field'],
                    'error_code': error['error_code'],
                    'message': error['error']
                })
        
        student_id = row_data.get('student_id')
        if student_id:
            id_result = self.validate_student_id(student_id)
            if not id_result['valid']:
                result['valid'] = False
                result['errors'].append({
                    'row': row_index,
                    'field': 'student_id',
                    'value': str(student_id),
                    'error_code': id_result['error_code'],
                    'message': id_result['error']
                })
        
        for field, (min_val, max_val) in self.SCORE_RANGES.items():
            value = row_data.get(field)
            if value is not None and value != '':
                range_result = self.validate_score_range(field, value)
                if not range_result['valid']:
                    result['valid'] = False
                    result['errors'].append({
                        'row': row_index,
                        'field': field,
                        'value': value,
                        'error_code': range_result['error_code'],
                        'message': range_result['error']
                    })
        
        if result['errors']:
            logger.debug(f"第{row_index}行数据验证失败: {len(result['errors'])}个错误")
        
        return result
    
    def generate_validation_report(self, results: List[Dict]) -> Dict[str, Any]:
        """生成校验报告
        
        汇总所有行的验证结果，生成统计报告。
        
        Args:
            results: 各行验证结果列表
            
        Returns:
            {
                'total_rows': int,  # 总行数
                'valid_rows': int,  # 有效行数
                'invalid_rows': int,  # 无效行数
                'error_count': int,  # 总错误数
                'error_summary': Dict[str, int],  # 错误类型统计
                'errors_by_row': Dict[int, List],  # 按行分组的错误
                'details': List[Dict],  # 详细错误列表
            }
        """
        report = {
            'total_rows': len(results),
            'valid_rows': 0,
            'invalid_rows': 0,
            'error_count': 0,
            'error_summary': {},
            'errors_by_row': {},
            'details': []
        }
        
        for result in results:
            row_index = result.get('row_index', 0)
            
            if result['valid']:
                report['valid_rows'] += 1
            else:
                report['invalid_rows'] += 1
                report['errors_by_row'][row_index] = result['errors']
            
            for error in result.get('errors', []):
                report['error_count'] += 1
                report['details'].append(error)
                
                error_code = error.get('error_code', 'unknown')
                error_key = str(error_code)
                report['error_summary'][error_key] = report['error_summary'].get(error_key, 0) + 1
        
        error_code_names = {
            str(ErrorCode.DATA_MISSING_REQUIRED): '缺少必填字段',
            str(ErrorCode.DATA_INVALID_STUDENT_ID): '学号格式无效',
            str(ErrorCode.DATA_OUT_OF_RANGE): '数据超出范围',
            str(ErrorCode.DATA_INVALID_FORMAT): '数据格式无效',
        }
        
        named_summary = {}
        for code, count in report['error_summary'].items():
            name = error_code_names.get(code, f'错误代码{code}')
            named_summary[name] = count
        report['error_summary'] = named_summary
        
        logger.info(f"校验报告生成完成: 总行数={report['total_rows']}, 有效={report['valid_rows']}, 无效={report['invalid_rows']}")
        
        return report


class ScoreImportService:
    """成绩导入服务"""
    
    def __init__(self):
        """初始化服务"""
        logger.info("成绩导入服务已初始化")
    
    def _normalize_column_name(self, col_name: str) -> str:
        """标准化列名（去除空白、换行符，转小写用于比较）
        
        Args:
            col_name: 原始列名
            
        Returns:
            标准化后的列名
        """
        if pd.isna(col_name):
            return ""
        return str(col_name).strip().replace('\n', '').replace('\r', '')
    
    def _identify_columns(self, df: pd.DataFrame) -> ColumnMappingResult:
        """自动识别DataFrame的列标题并映射到标准字段
        
        支持模糊匹配和变体识别，返回列映射结果。
        
        Args:
            df: pandas DataFrame
            
        Returns:
            ColumnMappingResult: 列映射结果
        """
        result = ColumnMappingResult()
        df_columns = df.columns.tolist()
        
        logger.info(f"开始识别列标题，共 {len(df_columns)} 列")
        logger.debug(f"原始列标题: {df_columns}")
        
        matched_standard_columns: Set[str] = set()
        
        for idx, col in enumerate(df_columns):
            normalized_col = self._normalize_column_name(col)
            if not normalized_col:
                continue
            
            matched = False
            for standard_name, variants in COLUMN_VARIANTS.items():
                for variant in variants:
                    if normalized_col.lower() == variant.lower() or normalized_col == variant:
                        result.column_map[standard_name] = col
                        matched_standard_columns.add(standard_name)
                        logger.debug(f"列 '{col}' 映射到标准字段 '{standard_name}'")
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                result.unrecognized_columns.append(col)
                logger.debug(f"列 '{col}' 未能识别")
        
        for col in REQUIRED_COLUMNS:
            if col not in matched_standard_columns:
                result.missing_required.append(col)
        
        for col in RECOMMENDED_COLUMNS:
            if col not in matched_standard_columns:
                result.missing_recommended.append(col)
        
        total_standard_columns = len(COLUMN_VARIANTS)
        result.confidence = len(matched_standard_columns) / total_standard_columns if total_standard_columns > 0 else 0.0
        
        if result.missing_required:
            logger.warning(f"缺少必需列: {result.missing_required}")
        
        if result.unrecognized_columns:
            logger.info(f"未识别的列: {result.unrecognized_columns}")
        
        logger.info(f"列识别完成，匹配率: {result.confidence:.2%}，匹配列数: {len(matched_standard_columns)}")
        
        return result
    
    def _try_index_mode(self, df: pd.DataFrame) -> bool:
        """尝试判断是否应该使用固定索引模式
        
        当列标题无法识别或识别率过低时，尝试使用固定索引模式。
        
        Args:
            df: pandas DataFrame
            
        Returns:
            是否应该使用索引模式
        """
        df_columns = df.columns.tolist()
        
        if len(df_columns) < len(REQUIRED_COLUMNS):
            return False
        
        first_col = self._normalize_column_name(df_columns[0]) if len(df_columns) > 0 else ""
        first_col_lower = first_col.lower()
        
        for variant in COLUMN_VARIANTS.get("学号", []):
            if first_col_lower == variant.lower():
                return False
        
        if first_col and not any(c.isdigit() for c in first_col):
            return False
        
        if len(df_columns) >= 24:
            return True
        
        return False
    
    def parse_excel_file(
        self, 
        file_path: str, 
        sheet_name: Optional[str] = None,
        force_index_mode: bool = False
    ) -> ParseResult:
        """解析Excel文件
        
        支持动态列标题识别和固定索引两种解析方式。
        优先使用动态列标题识别，当识别失败或用户指定时使用固定索引模式。
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称，如果为None则读取第一个工作表
            force_index_mode: 是否强制使用固定索引模式
            
        Returns:
            ParseResult: 解析结果，包含成绩数据、验证报告等信息
            
        Raises:
            FileUploadException: 文件解析失败
        """
        result = ParseResult()
        
        try:
            logger.info(f"开始解析Excel文件: {file_path}")
            
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            result.total_rows = len(df)
            logger.info(f"Excel文件读取成功，共 {result.total_rows} 行数据，{len(df.columns)} 列")
            
            if force_index_mode:
                logger.info("使用强制索引模式")
                result.column_mapping = self._create_index_mapping()
                result.column_mapping.use_index_mode = True
            else:
                result.column_mapping = self._identify_columns(df)
                
                if result.column_mapping.missing_required:
                    if self._try_index_mode(df):
                        logger.info("列标题识别缺少必需列，尝试使用固定索引模式")
                        result.column_mapping = self._create_index_mapping()
                        result.column_mapping.use_index_mode = True
                        result.warnings.append("使用固定索引模式解析（列标题识别不完整）")
            
            if result.column_mapping.use_index_mode:
                if result.total_rows > 0 and len(df.columns) < max(TABLE_MAP.values()) + 1:
                    error_msg = f"固定索引模式需要至少 {max(TABLE_MAP.values()) + 1} 列，当前只有 {len(df.columns)} 列"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
                    return result
            else:
                if result.column_mapping.missing_required:
                    error_msg = f"缺少必需列: {', '.join(result.column_mapping.missing_required)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
                    return result
            
            for idx, row in df.iterrows():
                try:
                    score_data = self._parse_row(row, result.column_mapping)
                    if score_data:
                        result.scores.append(score_data)
                        result.success_rows += 1
                    else:
                        result.failed_rows += 1
                except Exception as e:
                    result.failed_rows += 1
                    warning_msg = f"解析第 {idx + 2} 行数据失败: {e}"
                    result.warnings.append(warning_msg)
                    logger.warning(warning_msg)
                    continue
            
            if result.column_mapping.missing_recommended:
                result.warnings.append(f"缺少推荐列: {', '.join(result.column_mapping.missing_recommended)}")
            
            if result.column_mapping.unrecognized_columns:
                result.warnings.append(f"未识别的列: {', '.join(result.column_mapping.unrecognized_columns)}")
            
            logger.info(f"解析完成: 成功 {result.success_rows} 条，失败 {result.failed_rows} 条")
            
        except Exception as e:
            error_msg = f"解析Excel文件失败: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            raise FileUploadException(error_msg)
        
        return result
    
    def _create_index_mapping(self) -> ColumnMappingResult:
        """创建固定索引模式的列映射
        
        Returns:
            ColumnMappingResult: 使用固定索引的列映射结果
        """
        result = ColumnMappingResult()
        result.use_index_mode = True
        
        for standard_name, idx in TABLE_MAP.items():
            result.column_map[standard_name] = idx
        
        for col in REQUIRED_COLUMNS:
            if col not in result.column_map:
                result.missing_required.append(col)
        
        result.confidence = 1.0
        logger.info("已创建固定索引模式映射")
        
        return result
    
    def _parse_row(
        self, 
        row: pd.Series, 
        column_mapping: ColumnMappingResult
    ) -> Optional[Dict[str, Any]]:
        """解析单行数据
        
        Args:
            row: pandas DataFrame的一行
            column_mapping: 列映射结果
            
        Returns:
            解析后的成绩数据字典
        """
        column_map = column_mapping.column_map
        
        if column_mapping.use_index_mode:
            student_id = self._get_value_by_index(row, TABLE_MAP["学号"])
        else:
            col_name = column_map.get("学号")
            student_id = self._get_value_by_name(row, col_name) if col_name else None
        
        if not student_id or pd.isna(student_id):
            return None
        
        score_data = {
            "student_id": str(student_id).strip(),
            "student_name": self._get_field_value(row, column_map, "姓名", "", use_index_mode=column_mapping.use_index_mode),
            
            "total_score": self._get_field_float_value(row, column_map, "总分", 0.0, use_index_mode=column_mapping.use_index_mode),
            "total_required_credits": self._get_field_float_value(row, column_map, "总应获得学分", 0.0, use_index_mode=column_mapping.use_index_mode),
            "course_count": self._get_field_int_value(row, column_map, "门数", 0, use_index_mode=column_mapping.use_index_mode),
            "total_credits": self._get_field_float_value(row, column_map, "总学分", 0.0, use_index_mode=column_mapping.use_index_mode),
            "earned_credits": self._get_field_float_value(row, column_map, "获得学分", 0.0, use_index_mode=column_mapping.use_index_mode),
            "failed_credits": self._get_field_float_value(row, column_map, "不及格学分", 0.0, use_index_mode=column_mapping.use_index_mode),
            
            "pass_rate": self._get_field_float_value(row, column_map, "通过率", 0.0, use_index_mode=column_mapping.use_index_mode),
            "arithmetic_average": self._get_field_float_value(row, column_map, "算术平均分", 0.0, use_index_mode=column_mapping.use_index_mode),
            "arithmetic_average_rank": self._get_field_int_value(row, column_map, "算术平均分排名", None, use_index_mode=column_mapping.use_index_mode),
            
            "weighted_average": self._get_field_float_value(row, column_map, "学分加权平均分", 0.0, use_index_mode=column_mapping.use_index_mode),
            "weighted_average_rank": self._get_field_int_value(row, column_map, "学分加权平均分排名", None, use_index_mode=column_mapping.use_index_mode),
            
            "average_gpa": self._get_field_float_value(row, column_map, "平均绩点", 0.0, use_index_mode=column_mapping.use_index_mode),
            "average_gpa_rank": self._get_field_int_value(row, column_map, "平均绩点排名", None, use_index_mode=column_mapping.use_index_mode),
            "average_credit_gpa": self._get_field_float_value(row, column_map, "平均学分绩点", 0.0, use_index_mode=column_mapping.use_index_mode),
            "average_credit_gpa_rank": self._get_field_int_value(row, column_map, "平均学分绩点排名", None, use_index_mode=column_mapping.use_index_mode),
            "credit_gpa_sum": self._get_field_float_value(row, column_map, "学分绩点和", 0.0, use_index_mode=column_mapping.use_index_mode),
            "credit_gpa_sum_rank": self._get_field_int_value(row, column_map, "学分绩点和排名", None, use_index_mode=column_mapping.use_index_mode),
            
            "failed_course_count": self._get_field_int_value(row, column_map, "不及格门次", 0, use_index_mode=column_mapping.use_index_mode),
            
            "college": self._get_field_value(row, column_map, "学院", "", use_index_mode=column_mapping.use_index_mode),
            "grade": self._get_field_value(row, column_map, "年级", "", use_index_mode=column_mapping.use_index_mode),
            "major": self._get_field_value(row, column_map, "专业", "", use_index_mode=column_mapping.use_index_mode),
            "class_name": self._get_field_value(row, column_map, "班级", "", use_index_mode=column_mapping.use_index_mode),
        }
        
        return score_data
    
    def _get_field_value(
        self, 
        row: pd.Series, 
        column_map: Dict[str, Any], 
        standard_name: str, 
        default: Any = None,
        use_index_mode: bool = False
    ) -> Any:
        """根据标准字段名获取值
        
        Args:
            row: pandas Series
            column_map: 列映射字典
            standard_name: 标准字段名
            default: 默认值
            use_index_mode: 是否使用索引模式
            
        Returns:
            字段值
        """
        if standard_name not in column_map:
            return default
        
        if use_index_mode:
            return self._get_value_by_index(row, column_map[standard_name], default)
        else:
            return self._get_value_by_name(row, column_map[standard_name], default)
    
    def _get_field_float_value(
        self, 
        row: pd.Series, 
        column_map: Dict[str, Any], 
        standard_name: str, 
        default: float = 0.0,
        use_index_mode: bool = False
    ) -> float:
        """根据标准字段名获取浮点数值
        
        Args:
            row: pandas Series
            column_map: 列映射字典
            standard_name: 标准字段名
            default: 默认值
            use_index_mode: 是否使用索引模式
            
        Returns:
            浮点数值
        """
        value = self._get_field_value(row, column_map, standard_name, default, use_index_mode)
        return self._to_float(value, default)
    
    def _get_field_int_value(
        self, 
        row: pd.Series, 
        column_map: Dict[str, Any], 
        standard_name: str, 
        default: Optional[int] = None,
        use_index_mode: bool = False
    ) -> Optional[int]:
        """根据标准字段名获取整数值
        
        Args:
            row: pandas Series
            column_map: 列映射字典
            standard_name: 标准字段名
            default: 默认值
            use_index_mode: 是否使用索引模式
            
        Returns:
            整数值
        """
        value = self._get_field_value(row, column_map, standard_name, default, use_index_mode)
        return self._to_int(value, default)
    
    def _get_value_by_index(self, row: pd.Series, index: int, default: Any = None) -> Any:
        """通过索引安全获取行中的值
        
        Args:
            row: pandas Series
            index: 列索引
            default: 默认值
            
        Returns:
            值或默认值
        """
        try:
            if index < len(row):
                value = row.iloc[index]
                if pd.isna(value):
                    return default
                return value
            return default
        except Exception:
            return default
    
    def _get_value_by_name(self, row: pd.Series, col_name: str, default: Any = None) -> Any:
        """通过列名安全获取行中的值
        
        Args:
            row: pandas Series
            col_name: 列名
            default: 默认值
            
        Returns:
            值或默认值
        """
        try:
            if col_name in row.index:
                value = row[col_name]
                if pd.isna(value):
                    return default
                return value
            return default
        except Exception:
            return default
    
    def _to_float(self, value: Any, default: float = 0.0) -> float:
        """将值转换为浮点数
        
        Args:
            value: 原始值
            default: 默认值
            
        Returns:
            浮点数值
        """
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                value = value.replace('%', '').strip()
                return float(value)
            return default
        except (ValueError, TypeError):
            return default
    
    def _to_int(self, value: Any, default: Optional[int] = None) -> Optional[int]:
        """将值转换为整数
        
        Args:
            value: 原始值
            default: 默认值
            
        Returns:
            整数值
        """
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                value = value.strip()
                if value:
                    return int(float(value))
            return default
        except (ValueError, TypeError):
            return default
    
    def _get_value(self, row: pd.Series, index: int, default: Any = None) -> Any:
        """安全获取行中的值（向后兼容方法）
        
        Args:
            row: pandas Series
            index: 列索引
            default: 默认值
            
        Returns:
            值或默认值
        """
        return self._get_value_by_index(row, index, default)
    
    def _get_float_value(self, row: pd.Series, index: int, default: float = 0.0) -> float:
        """获取浮点数值（向后兼容方法）
        
        Args:
            row: pandas Series
            index: 列索引
            default: 默认值
            
        Returns:
            浮点数值
        """
        value = self._get_value(row, index, default)
        return self._to_float(value, default)
    
    def _get_int_value(self, row: pd.Series, index: int, default: Optional[int] = None) -> Optional[int]:
        """获取整数值（向后兼容方法）
        
        Args:
            row: pandas Series
            index: 列索引
            default: 默认值
            
        Returns:
            整数值
        """
        value = self._get_value(row, index, default)
        return self._to_int(value, default)
    
    def validate_score_data(self, score_data: Dict[str, Any]) -> bool:
        """验证成绩数据
        
        Args:
            score_data: 成绩数据
            
        Returns:
            是否有效
        """
        if not score_data.get("student_id"):
            logger.warning("缺少学号")
            return False
        
        if not score_data.get("student_name"):
            logger.warning(f"学号 {score_data['student_id']} 缺少姓名")
            return False
        
        return True
    
    def validate_excel_columns(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """验证Excel文件的列标题
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            验证结果字典
        """
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            mapping_result = self._identify_columns(df)
            
            return {
                "valid": len(mapping_result.missing_required) == 0,
                "total_columns": len(df.columns),
                "recognized_columns": list(mapping_result.column_map.keys()),
                "unrecognized_columns": mapping_result.unrecognized_columns,
                "missing_required": mapping_result.missing_required,
                "missing_recommended": mapping_result.missing_recommended,
                "confidence": mapping_result.confidence,
                "can_use_index_mode": self._try_index_mode(df),
                "column_count": len(df.columns),
                "min_required_columns": max(TABLE_MAP.values()) + 1 if TABLE_MAP else 0
            }
        except Exception as e:
            logger.error(f"验证Excel列标题失败: {e}", exc_info=True)
            return {
                "valid": False,
                "error": str(e)
            }


_score_import_service_instance: Optional[ScoreImportService] = None
_excel_structure_validator_instance: Optional[ExcelStructureValidator] = None
_data_validator_instance: Optional[DataValidator] = None


def get_score_import_service() -> ScoreImportService:
    """获取成绩导入服务单例"""
    global _score_import_service_instance
    if _score_import_service_instance is None:
        _score_import_service_instance = ScoreImportService()
    return _score_import_service_instance


def get_excel_structure_validator() -> ExcelStructureValidator:
    """获取Excel结构验证器单例"""
    global _excel_structure_validator_instance
    if _excel_structure_validator_instance is None:
        _excel_structure_validator_instance = ExcelStructureValidator()
    return _excel_structure_validator_instance


def get_data_validator() -> DataValidator:
    """获取数据校验器单例"""
    global _data_validator_instance
    if _data_validator_instance is None:
        _data_validator_instance = DataValidator()
    return _data_validator_instance
