#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成绩导入服务

提供Excel成绩文件的解析和导入功能。
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.logger import logger
from app.core.exceptions import FileUploadException


# Excel列索引映射
TABLE_MAP = {
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


class ScoreImportService:
    """成绩导入服务"""
    
    def __init__(self):
        """初始化服务"""
        logger.info("成绩导入服务已初始化")
    
    def parse_excel_file(self, file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """解析Excel文件
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称，如果为None则读取第一个工作表
            
        Returns:
            解析后的成绩数据列表
            
        Raises:
            FileUploadException: 文件解析失败
        """
        try:
            # 读取Excel文件
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            logger.info(f"Excel文件读取成功，共 {len(df)} 行数据")
            
            # 解析数据
            scores = []
            for idx, row in df.iterrows():
                try:
                    score_data = self._parse_row(row)
                    if score_data:
                        scores.append(score_data)
                except Exception as e:
                    logger.warning(f"解析第 {idx + 2} 行数据失败: {e}")
                    continue
            
            logger.info(f"成功解析 {len(scores)} 条成绩数据")
            return scores
        
        except Exception as e:
            logger.error(f"解析Excel文件失败: {e}", exc_info=True)
            raise FileUploadException(f"解析Excel文件失败: {str(e)}")
    
    def _parse_row(self, row) -> Optional[Dict[str, Any]]:
        """解析单行数据
        
        Args:
            row: pandas DataFrame的一行
            
        Returns:
            解析后的成绩数据字典
        """
        # 获取学号，如果学号为空则跳过
        student_id = self._get_value(row, TABLE_MAP["学号"])
        if not student_id or pd.isna(student_id):
            return None
        
        # 构建成绩数据
        score_data = {
            "student_id": str(student_id).strip(),
            "student_name": str(self._get_value(row, TABLE_MAP["姓名"], "")).strip(),
            
            # 成绩信息
            "total_score": self._get_float_value(row, TABLE_MAP["总分"], 0.0),
            "total_required_credits": self._get_float_value(row, TABLE_MAP["总应获得学分"], 0.0),
            "course_count": self._get_int_value(row, TABLE_MAP["门数"], 0),
            "total_credits": self._get_float_value(row, TABLE_MAP["总学分"], 0.0),
            "earned_credits": self._get_float_value(row, TABLE_MAP["获得学分"], 0.0),
            "failed_credits": self._get_float_value(row, TABLE_MAP["不及格学分"], 0.0),
            
            # 通过率和平均分
            "pass_rate": self._get_float_value(row, TABLE_MAP["通过率"], 0.0),
            "arithmetic_average": self._get_float_value(row, TABLE_MAP["算术平均分"], 0.0),
            "arithmetic_average_rank": self._get_int_value(row, TABLE_MAP["算术平均分排名"], None),
            
            # 学分加权平均分
            "weighted_average": self._get_float_value(row, TABLE_MAP["学分加权平均分"], 0.0),
            "weighted_average_rank": self._get_int_value(row, TABLE_MAP["学分加权平均分排名"], None),
            
            # 绩点相关
            "average_gpa": self._get_float_value(row, TABLE_MAP["平均绩点"], 0.0),
            "average_gpa_rank": self._get_int_value(row, TABLE_MAP["平均绩点排名"], None),
            "average_credit_gpa": self._get_float_value(row, TABLE_MAP["平均学分绩点"], 0.0),
            "average_credit_gpa_rank": self._get_int_value(row, TABLE_MAP["平均学分绩点排名"], None),
            "credit_gpa_sum": self._get_float_value(row, TABLE_MAP["学分绩点和"], 0.0),
            "credit_gpa_sum_rank": self._get_int_value(row, TABLE_MAP["学分绩点和排名"], None),
            
            # 其他统计
            "failed_course_count": self._get_int_value(row, TABLE_MAP["不及格门次"], 0),
            
            # 基本信息
            "college": str(self._get_value(row, TABLE_MAP["学院"], "")).strip(),
            "grade": str(self._get_value(row, TABLE_MAP["年级"], "")).strip(),
            "major": str(self._get_value(row, TABLE_MAP["专业"], "")).strip(),
            "class_name": str(self._get_value(row, TABLE_MAP["班级"], "")).strip(),
        }
        
        return score_data
    
    def _get_value(self, row, index: int, default=None):
        """安全获取行中的值
        
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
    
    def _get_float_value(self, row, index: int, default: float = 0.0) -> float:
        """获取浮点数值
        
        Args:
            row: pandas Series
            index: 列索引
            default: 默认值
            
        Returns:
            浮点数值
        """
        value = self._get_value(row, index, default)
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # 移除百分号等符号
                value = value.replace('%', '').strip()
                return float(value)
            return default
        except (ValueError, TypeError):
            return default
    
    def _get_int_value(self, row, index: int, default: Optional[int] = None) -> Optional[int]:
        """获取整数值
        
        Args:
            row: pandas Series
            index: 列索引
            default: 默认值
            
        Returns:
            整数值
        """
        value = self._get_value(row, index, default)
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
    
    def validate_score_data(self, score_data: Dict[str, Any]) -> bool:
        """验证成绩数据
        
        Args:
            score_data: 成绩数据
            
        Returns:
            是否有效
        """
        # 必须字段检查
        if not score_data.get("student_id"):
            logger.warning("缺少学号")
            return False
        
        if not score_data.get("student_name"):
            logger.warning(f"学号 {score_data['student_id']} 缺少姓名")
            return False
        
        return True


# 全局单例
_score_import_service_instance: Optional[ScoreImportService] = None


def get_score_import_service() -> ScoreImportService:
    """获取成绩导入服务单例"""
    global _score_import_service_instance
    if _score_import_service_instance is None:
        _score_import_service_instance = ScoreImportService()
    return _score_import_service_instance

