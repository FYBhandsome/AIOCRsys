#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准错误响应格式定义模块
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime


class ErrorDetail(BaseModel):
    code: int
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    suggestion: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: int
    error_message: str
    details: Optional[List[ErrorDetail]] = None
    trace_id: Optional[str] = None
    timestamp: Optional[str] = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None
    trace_id: Optional[str] = None
    timestamp: Optional[str] = None


def generate_trace_id() -> str:
    return str(uuid.uuid4())[:8]


def create_error_response(
    error_code: int,
    error_message: str,
    details: Optional[List[ErrorDetail]] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()
    
    response = {
        "success": False,
        "error_code": error_code,
        "error_message": error_message,
        "trace_id": trace_id,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = [d.model_dump(exclude_none=True) for d in details]
    
    return response


def create_success_response(
    message: str,
    data: Optional[Any] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()
    
    response = {
        "success": True,
        "message": message,
        "trace_id": trace_id,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response


def create_file_error_detail(
    code: int,
    message: str,
    field: Optional[str] = None,
    value: Optional[Any] = None,
    suggestion: Optional[str] = None
) -> ErrorDetail:
    return ErrorDetail(
        code=code,
        message=message,
        field=field,
        value=value,
        suggestion=suggestion
    )


def create_validation_error_details(
    errors: List[Dict[str, Any]]
) -> List[ErrorDetail]:
    details = []
    for error in errors:
        detail = ErrorDetail(
            code=error.get("code", 3002),
            message=error.get("message", "验证失败"),
            field=error.get("field"),
            value=error.get("value"),
            suggestion=error.get("suggestion")
        )
        details.append(detail)
    return details
