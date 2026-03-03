#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义异常处理模块
"""

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict, List, Optional

from app.core.logger import logger
from app.core.error_codes import ErrorCode, get_error_message, get_error_suggestion
from app.core.error_response import (
    ErrorDetail,
    create_error_response,
    generate_trace_id
)


class FileValidationError(HTTPException):
    def __init__(
        self,
        error_code: int = ErrorCode.FILE_INVALID_FORMAT,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        self.error_code = error_code
        self.message = message or get_error_message(error_code)
        self.suggestion = get_error_suggestion(error_code)
        self.filename = filename
        self.details = details or []
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=self.message
        )


class ExcelParseError(HTTPException):
    def __init__(
        self,
        error_code: int = ErrorCode.EXCEL_READ_ERROR,
        message: Optional[str] = None,
        sheet_name: Optional[str] = None,
        missing_columns: Optional[List[str]] = None,
        row_number: Optional[int] = None,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        self.error_code = error_code
        self.message = message or get_error_message(error_code)
        self.suggestion = get_error_suggestion(error_code)
        self.sheet_name = sheet_name
        self.missing_columns = missing_columns
        self.row_number = row_number
        self.details = details or []
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=self.message
        )


class DataValidationError(HTTPException):
    def __init__(
        self,
        error_code: int = ErrorCode.DATA_INVALID_FORMAT,
        message: Optional[str] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        row_number: Optional[int] = None,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        self.error_code = error_code
        self.message = message or get_error_message(error_code)
        self.suggestion = get_error_suggestion(error_code)
        self.field = field
        self.value = value
        self.row_number = row_number
        self.details = details or []
        
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=self.message
        )


class BusinessError(HTTPException):
    def __init__(
        self,
        error_code: int = ErrorCode.OPERATION_FAILED,
        message: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        self.error_code = error_code
        self.message = message or get_error_message(error_code)
        self.suggestion = get_error_suggestion(error_code)
        self.details = details or []
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=self.message
        )


class FileUploadException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class OCRProcessingException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class StudentNotFoundException(HTTPException):
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.error_code = ErrorCode.STUDENT_NOT_FOUND
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"学生不存在: {student_id}"
        )


class ClassNotFoundException(HTTPException):
    def __init__(self, class_id: str):
        self.class_id = class_id
        self.error_code = ErrorCode.CLASS_NOT_FOUND
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"班级不存在: {class_id}"
        )


class ValidationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class DatabaseException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


async def validation_exception_handler(request, exc: RequestValidationError):
    trace_id = generate_trace_id()
    errors = exc.errors()
    
    logger.warning(f"[{trace_id}] 验证失败: {errors}")
    
    details = []
    for error in errors:
        loc = error.get("loc", [])
        field = ".".join(str(x) for x in loc) if loc else None
        
        detail = ErrorDetail(
            code=ErrorCode.DATA_INVALID_FORMAT,
            message=error.get("msg", "验证失败"),
            field=field,
            value=str(error.get("input", ""))[:100] if error.get("input") else None,
            suggestion="请检查输入格式是否正确"
        )
        details.append(detail)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            error_code=ErrorCode.DATA_INVALID_FORMAT,
            error_message="请求数据验证失败",
            details=details,
            trace_id=trace_id
        )
    )


async def file_validation_exception_handler(request, exc: FileValidationError):
    trace_id = generate_trace_id()
    
    logger.warning(f"[{trace_id}] 文件验证失败: {exc.message}, 文件: {exc.filename}")
    
    details = []
    if exc.filename:
        details.append(ErrorDetail(
            code=exc.error_code,
            message=exc.message,
            field="filename",
            value=exc.filename,
            suggestion=exc.suggestion
        ))
    
    if exc.details:
        for d in exc.details:
            details.append(ErrorDetail(
                code=d.get("code", exc.error_code),
                message=d.get("message", exc.message),
                field=d.get("field"),
                value=d.get("value"),
                suggestion=d.get("suggestion", exc.suggestion)
            ))
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error_code=exc.error_code,
            error_message=exc.message,
            details=details if details else None,
            trace_id=trace_id
        )
    )


async def excel_parse_exception_handler(request, exc: ExcelParseError):
    trace_id = generate_trace_id()
    
    logger.warning(
        f"[{trace_id}] Excel解析失败: {exc.message}, "
        f"工作表: {exc.sheet_name}, 行号: {exc.row_number}"
    )
    
    details = []
    
    if exc.missing_columns:
        details.append(ErrorDetail(
            code=ErrorCode.EXCEL_MISSING_COLUMNS,
            message=f"缺少必要的列: {', '.join(exc.missing_columns)}",
            field="columns",
            value=exc.missing_columns,
            suggestion="请确保Excel包含所有必要的列"
        ))
    
    if exc.row_number:
        details.append(ErrorDetail(
            code=exc.error_code,
            message=exc.message,
            field="row",
            value=exc.row_number,
            suggestion=exc.suggestion
        ))
    
    if exc.details:
        for d in exc.details:
            details.append(ErrorDetail(
                code=d.get("code", exc.error_code),
                message=d.get("message", exc.message),
                field=d.get("field"),
                value=d.get("value"),
                suggestion=d.get("suggestion", exc.suggestion)
            ))
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error_code=exc.error_code,
            error_message=exc.message,
            details=details if details else None,
            trace_id=trace_id
        )
    )


async def data_validation_exception_handler(request, exc: DataValidationError):
    trace_id = generate_trace_id()
    
    logger.warning(
        f"[{trace_id}] 数据验证失败: {exc.message}, "
        f"字段: {exc.field}, 值: {exc.value}, 行号: {exc.row_number}"
    )
    
    details = []
    
    if exc.field:
        details.append(ErrorDetail(
            code=exc.error_code,
            message=exc.message,
            field=exc.field,
            value=str(exc.value)[:100] if exc.value else None,
            suggestion=exc.suggestion
        ))
    
    if exc.details:
        for d in exc.details:
            details.append(ErrorDetail(
                code=d.get("code", exc.error_code),
                message=d.get("message", exc.message),
                field=d.get("field"),
                value=d.get("value"),
                suggestion=d.get("suggestion", exc.suggestion)
            ))
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            error_code=exc.error_code,
            error_message=exc.message,
            details=details if details else None,
            trace_id=trace_id
        )
    )


async def business_exception_handler(request, exc: BusinessError):
    trace_id = generate_trace_id()
    
    logger.warning(f"[{trace_id}] 业务错误: {exc.message}")
    
    details = []
    if exc.details:
        for d in exc.details:
            details.append(ErrorDetail(
                code=d.get("code", exc.error_code),
                message=d.get("message", exc.message),
                field=d.get("field"),
                value=d.get("value"),
                suggestion=d.get("suggestion", exc.suggestion)
            ))
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error_code=exc.error_code,
            error_message=exc.message,
            details=details if details else None,
            trace_id=trace_id
        )
    )


async def http_exception_handler(request, exc: HTTPException):
    trace_id = generate_trace_id()
    
    logger.error(f"[{trace_id}] HTTP异常: {exc.detail}")
    
    error_code = ErrorCode.INTERNAL_ERROR
    if exc.status_code == 404:
        error_code = ErrorCode.OPERATION_FAILED
    elif exc.status_code == 401:
        error_code = ErrorCode.AUTH_UNAUTHORIZED
    elif exc.status_code == 403:
        error_code = ErrorCode.AUTH_FORBIDDEN
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=error_code,
            error_message=str(exc.detail),
            trace_id=trace_id
        )
    )


async def general_exception_handler(request, exc: Exception):
    trace_id = generate_trace_id()
    
    logger.error(f"[{trace_id}] 未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            error_message="服务器内部错误，请稍后重试",
            trace_id=trace_id
        )
    )
