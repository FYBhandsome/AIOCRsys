#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入模块
提供FastAPI依赖注入函数
"""
from app.services.database_tortoise import get_db_service as _get_db_service
from app.services.student_service import get_student_service as _get_student_service
from app.services.class_service import get_class_service as _get_class_service
from app.services.upload_service import get_upload_service as _get_upload_service


def get_db_service():
    """获取数据库服务实例"""
    return _get_db_service()


def get_student_service():
    """获取学生服务实例"""
    return _get_student_service()


def get_class_service():
    """获取班级服务实例"""
    return _get_class_service()


def get_upload_service():
    """获取文件上传服务实例"""
    return _get_upload_service()