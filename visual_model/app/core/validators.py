#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求参数验证模块
定义通用的请求参数模型和验证器
"""
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from datetime import datetime
from enum import Enum
import re

from pydantic import BaseModel, Field, field_validator, model_validator
from fastapi import Query, Path, Body, Header, Depends


class SortOrder(str, Enum):
    """排序顺序"""
    ASC = "asc"
    DESC = "desc"


class BaseRequest(BaseModel):
    """基础请求模型"""
    
    class Config:
        extra = "forbid"
        str_strip_whitespace = True


class PaginationRequest(BaseRequest):
    """分页请求参数"""
    
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    
    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        if v > 100:
            return 100
        return v


class SortRequest(BaseRequest):
    """排序请求参数"""
    
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="排序顺序")


class SearchRequest(BaseRequest):
    """搜索请求参数"""
    
    keyword: Optional[str] = Field(default=None, max_length=100, description="搜索关键词")
    fields: Optional[List[str]] = Field(default=None, description="搜索字段列表")


class FilterRequest(BaseRequest):
    """过滤请求参数"""
    
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    exclude: Optional[Dict[str, Any]] = Field(default=None, description="排除条件")


class DateRangeRequest(BaseRequest):
    """日期范围请求参数"""
    
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    
    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("开始日期不能晚于结束日期")
        return self


class IDRequest(BaseRequest):
    """ID请求参数"""
    
    id: int = Field(..., gt=0, description="记录ID")


class IDsRequest(BaseRequest):
    """批量ID请求参数"""
    
    ids: List[int] = Field(..., min_length=1, max_length=100, description="ID列表")


class StudentIDRequest(BaseRequest):
    """学号请求参数"""
    
    student_id: str = Field(..., min_length=1, max_length=50, description="学号")
    
    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9\-_]+$", v):
            raise ValueError("学号只能包含字母、数字、横线和下划线")
        return v


class AcademicYearRequest(BaseRequest):
    """学年请求参数"""
    
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$", description="学年，格式：2024-2025")
    
    @field_validator("academic_year")
    @classmethod
    def validate_academic_year(cls, v: str) -> str:
        parts = v.split("-")
        if len(parts) != 2:
            raise ValueError("学年格式错误，应为：YYYY-YYYY")
        
        year1, year2 = int(parts[0]), int(parts[1])
        if year2 != year1 + 1:
            raise ValueError("学年必须是连续的两个年份")
        
        return v


class SemesterRequest(BaseRequest):
    """学期请求参数"""
    
    semester: str = Field(..., pattern=r"^(春|秋)季学期$", description="学期")


class ClassRequest(BaseRequest):
    """班级请求参数"""
    
    class_name: str = Field(..., min_length=1, max_length=50, description="班级名称")


class FileUploadRequest(BaseRequest):
    """文件上传请求参数"""
    
    file_type: str = Field(..., description="文件类型")
    description: Optional[str] = Field(default=None, max_length=500, description="文件描述")
    
    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        allowed_types = ["image", "document", "excel", "pdf", "certificate"]
        if v not in allowed_types:
            raise ValueError(f"文件类型必须是: {', '.join(allowed_types)}")
        return v


class ChunkUploadRequest(BaseRequest):
    """分片上传请求参数"""
    
    file_id: str = Field(..., description="文件唯一标识")
    chunk_index: int = Field(..., ge=0, description="分片索引")
    total_chunks: int = Field(..., ge=1, description="总分片数")
    chunk_hash: Optional[str] = Field(default=None, description="分片哈希值")


class CertificateUploadRequest(BaseRequest):
    """证书上传请求参数"""
    
    student_id: str = Field(..., description="学号")
    certificate_type: str = Field(..., description="证书类型")
    issue_date: Optional[datetime] = Field(default=None, description="发证日期")
    issuer: Optional[str] = Field(default=None, max_length=100, description="发证机构")
    description: Optional[str] = Field(default=None, max_length=500, description="证书描述")
    
    @field_validator("certificate_type")
    @classmethod
    def validate_certificate_type(cls, v: str) -> str:
        allowed_types = ["竞赛", "证书", "荣誉", "技能", "其他"]
        if v not in allowed_types:
            raise ValueError(f"证书类型必须是: {', '.join(allowed_types)}")
        return v


class ScoreQueryRequest(
    StudentIDRequest,
    AcademicYearRequest,
    SemesterRequest
):
    """成绩查询请求参数"""
    pass


class ComprehensiveScoreRequest(BaseRequest):
    """综测成绩请求参数"""
    
    student_id: str = Field(..., description="学号")
    academic_year: str = Field(..., description="学年")
    semester: str = Field(..., description="学期")
    moral_score: Optional[float] = Field(default=None, ge=0, le=100, description="德育分")
    intellectual_score: Optional[float] = Field(default=None, ge=0, le=100, description="智育分")
    physical_score: Optional[float] = Field(default=None, ge=0, le=100, description="体育分")
    aesthetic_score: Optional[float] = Field(default=None, ge=0, le=100, description="美育分")
    labor_score: Optional[float] = Field(default=None, ge=0, le=100, description="劳育分")
    bonus_score: Optional[float] = Field(default=0, ge=0, description="加分")
    penalty_score: Optional[float] = Field(default=0, ge=0, description="扣分")


class BatchOperationRequest(BaseRequest):
    """批量操作请求参数"""
    
    operation: str = Field(..., description="操作类型")
    target_ids: List[int] = Field(..., min_length=1, max_length=100, description="目标ID列表")
    params: Optional[Dict[str, Any]] = Field(default=None, description="操作参数")


T = TypeVar("T")


class CommonQueryParams:
    """通用查询参数依赖"""
    
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
        sort_by: Optional[str] = Query(default=None, description="排序字段"),
        sort_order: SortOrder = Query(default=SortOrder.DESC, description="排序顺序"),
        keyword: Optional[str] = Query(default=None, max_length=100, description="搜索关键词")
    ):
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.keyword = keyword


def get_pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
) -> PaginationRequest:
    """获取分页参数依赖"""
    return PaginationRequest(page=page, page_size=page_size)


def get_sort(
    sort_by: Optional[str] = Query(default=None),
    sort_order: SortOrder = Query(default=SortOrder.DESC)
) -> SortRequest:
    """获取排序参数依赖"""
    return SortRequest(sort_by=sort_by, sort_order=sort_order)


def get_search(
    keyword: Optional[str] = Query(default=None, max_length=100)
) -> SearchRequest:
    """获取搜索参数依赖"""
    return SearchRequest(keyword=keyword)


def validate_id(
    id: int = Path(..., gt=0, description="记录ID")
) -> IDRequest:
    """验证ID参数依赖"""
    return IDRequest(id=id)


def validate_student_id(
    student_id: str = Path(..., min_length=1, max_length=50, description="学号")
) -> StudentIDRequest:
    """验证学号参数依赖"""
    return StudentIDRequest(student_id=student_id)


class RequestValidator:
    """请求验证器"""
    
    @staticmethod
    def validate_positive_int(value: int, field_name: str = "值") -> int:
        if value <= 0:
            raise ValueError(f"{field_name}必须为正整数")
        return value
    
    @staticmethod
    def validate_non_negative_float(value: float, field_name: str = "值") -> float:
        if value < 0:
            raise ValueError(f"{field_name}不能为负数")
        return value
    
    @staticmethod
    def validate_percentage(value: float, field_name: str = "值") -> float:
        if not 0 <= value <= 100:
            raise ValueError(f"{field_name}必须在0-100之间")
        return value
    
    @staticmethod
    def validate_date_not_future(value: datetime, field_name: str = "日期") -> datetime:
        if value > datetime.now():
            raise ValueError(f"{field_name}不能是未来日期")
        return value
    
    @staticmethod
    def validate_list_not_empty(value: List, field_name: str = "列表") -> List:
        if not value:
            raise ValueError(f"{field_name}不能为空")
        return value
    
    @staticmethod
    def validate_string_length(
        value: str,
        min_length: int = 0,
        max_length: int = None,
        field_name: str = "字符串"
    ) -> str:
        if len(value) < min_length:
            raise ValueError(f"{field_name}长度不能小于{min_length}")
        if max_length and len(value) > max_length:
            raise ValueError(f"{field_name}长度不能超过{max_length}")
        return value


validator = RequestValidator()
