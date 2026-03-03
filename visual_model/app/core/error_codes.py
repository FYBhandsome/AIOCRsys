#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准错误代码定义模块
"""


class ErrorCode:
    FILE_INVALID_FORMAT = 1001
    FILE_TOO_LARGE = 1002
    FILE_EMPTY = 1003
    FILE_PARSE_ERROR = 1004
    FILE_NOT_FOUND = 1005
    FILE_UPLOAD_FAILED = 1006
    
    EXCEL_MISSING_COLUMNS = 2001
    EXCEL_INVALID_DATA = 2002
    EXCEL_EMPTY_SHEET = 2003
    EXCEL_READ_ERROR = 2004
    EXCEL_SHEET_NOT_FOUND = 2005
    
    DATA_INVALID_STUDENT_ID = 3001
    DATA_MISSING_REQUIRED = 3002
    DATA_OUT_OF_RANGE = 3003
    DATA_INVALID_FORMAT = 3004
    DATA_DUPLICATE = 3005
    DATA_INVALID_SCORE = 3006
    
    STUDENT_NOT_FOUND = 4001
    SCORE_IMPORT_FAILED = 4002
    CLASS_NOT_FOUND = 4003
    COURSE_NOT_FOUND = 4004
    OPERATION_FAILED = 4005
    
    AUTH_UNAUTHORIZED = 5001
    AUTH_FORBIDDEN = 5002
    AUTH_TOKEN_EXPIRED = 5003
    AUTH_INVALID_TOKEN = 5004
    
    DATABASE_ERROR = 6001
    DATABASE_CONNECTION_ERROR = 6002
    DATABASE_QUERY_ERROR = 6003
    
    INTERNAL_ERROR = 9001
    UNKNOWN_ERROR = 9002


ERROR_MESSAGES = {
    ErrorCode.FILE_INVALID_FORMAT: "文件格式不支持",
    ErrorCode.FILE_TOO_LARGE: "文件大小超过限制",
    ErrorCode.FILE_EMPTY: "文件内容为空",
    ErrorCode.FILE_PARSE_ERROR: "文件解析失败",
    ErrorCode.FILE_NOT_FOUND: "文件不存在",
    ErrorCode.FILE_UPLOAD_FAILED: "文件上传失败",
    
    ErrorCode.EXCEL_MISSING_COLUMNS: "Excel缺少必要的列",
    ErrorCode.EXCEL_INVALID_DATA: "Excel数据格式无效",
    ErrorCode.EXCEL_EMPTY_SHEET: "Excel工作表为空",
    ErrorCode.EXCEL_READ_ERROR: "Excel读取失败",
    ErrorCode.EXCEL_SHEET_NOT_FOUND: "Excel工作表不存在",
    
    ErrorCode.DATA_INVALID_STUDENT_ID: "学号格式无效",
    ErrorCode.DATA_MISSING_REQUIRED: "缺少必填字段",
    ErrorCode.DATA_OUT_OF_RANGE: "数据超出有效范围",
    ErrorCode.DATA_INVALID_FORMAT: "数据格式无效",
    ErrorCode.DATA_DUPLICATE: "数据重复",
    ErrorCode.DATA_INVALID_SCORE: "成绩数据无效",
    
    ErrorCode.STUDENT_NOT_FOUND: "学生不存在",
    ErrorCode.SCORE_IMPORT_FAILED: "成绩导入失败",
    ErrorCode.CLASS_NOT_FOUND: "班级不存在",
    ErrorCode.COURSE_NOT_FOUND: "课程不存在",
    ErrorCode.OPERATION_FAILED: "操作失败",
    
    ErrorCode.AUTH_UNAUTHORIZED: "未授权访问",
    ErrorCode.AUTH_FORBIDDEN: "权限不足",
    ErrorCode.AUTH_TOKEN_EXPIRED: "登录已过期",
    ErrorCode.AUTH_INVALID_TOKEN: "无效的认证令牌",
    
    ErrorCode.DATABASE_ERROR: "数据库错误",
    ErrorCode.DATABASE_CONNECTION_ERROR: "数据库连接失败",
    ErrorCode.DATABASE_QUERY_ERROR: "数据库查询失败",
    
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
    ErrorCode.UNKNOWN_ERROR: "未知错误",
}


ERROR_SUGGESTIONS = {
    ErrorCode.FILE_INVALID_FORMAT: "请上传 .xlsx 或 .xls 格式的Excel文件",
    ErrorCode.FILE_TOO_LARGE: "请压缩文件或分批上传，最大支持10MB",
    ErrorCode.FILE_EMPTY: "请确保文件包含有效数据",
    ErrorCode.FILE_PARSE_ERROR: "请检查文件是否损坏，或尝试重新保存文件",
    ErrorCode.FILE_NOT_FOUND: "请重新上传文件",
    ErrorCode.FILE_UPLOAD_FAILED: "请检查网络连接后重试",
    
    ErrorCode.EXCEL_MISSING_COLUMNS: "请确保Excel包含学号、姓名、成绩等必要列",
    ErrorCode.EXCEL_INVALID_DATA: "请检查Excel中的数据格式是否正确",
    ErrorCode.EXCEL_EMPTY_SHEET: "请确保Excel工作表包含数据",
    ErrorCode.EXCEL_READ_ERROR: "请检查文件是否为有效的Excel格式",
    ErrorCode.EXCEL_SHEET_NOT_FOUND: "请检查工作表名称是否正确",
    
    ErrorCode.DATA_INVALID_STUDENT_ID: "学号应为数字或字母数字组合，长度通常为8-12位",
    ErrorCode.DATA_MISSING_REQUIRED: "请填写所有必填字段（学号、姓名、成绩等）",
    ErrorCode.DATA_OUT_OF_RANGE: "成绩应在0-100范围内",
    ErrorCode.DATA_INVALID_FORMAT: "请检查数据格式是否符合要求",
    ErrorCode.DATA_DUPLICATE: "该记录已存在，请检查是否重复导入",
    ErrorCode.DATA_INVALID_SCORE: "成绩应为数字，且在有效范围内",
    
    ErrorCode.STUDENT_NOT_FOUND: "请检查学号是否正确，或先导入学生信息",
    ErrorCode.SCORE_IMPORT_FAILED: "请检查数据格式后重试",
    ErrorCode.CLASS_NOT_FOUND: "请检查班级名称是否正确",
    ErrorCode.COURSE_NOT_FOUND: "请检查课程信息",
    ErrorCode.OPERATION_FAILED: "请稍后重试，或联系管理员",
    
    ErrorCode.AUTH_UNAUTHORIZED: "请先登录",
    ErrorCode.AUTH_FORBIDDEN: "您没有权限执行此操作",
    ErrorCode.AUTH_TOKEN_EXPIRED: "请重新登录",
    ErrorCode.AUTH_INVALID_TOKEN: "请重新登录",
    
    ErrorCode.DATABASE_ERROR: "请稍后重试，或联系管理员",
    ErrorCode.DATABASE_CONNECTION_ERROR: "数据库连接异常，请稍后重试",
    ErrorCode.DATABASE_QUERY_ERROR: "查询失败，请检查参数后重试",
    
    ErrorCode.INTERNAL_ERROR: "服务器异常，请稍后重试",
    ErrorCode.UNKNOWN_ERROR: "发生未知错误，请联系管理员",
}


def get_error_message(code: int) -> str:
    return ERROR_MESSAGES.get(code, "未知错误")


def get_error_suggestion(code: int) -> str:
    return ERROR_SUGGESTIONS.get(code, "请联系管理员获取帮助")


def get_error_info(code: int) -> dict:
    return {
        "code": code,
        "message": get_error_message(code),
        "suggestion": get_error_suggestion(code)
    }
