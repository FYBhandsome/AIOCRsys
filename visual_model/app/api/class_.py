#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
班级管理API路由
"""

from typing import List

from fastapi import APIRouter, Depends, Query

from app.api.api_utils import handle_api_errors, success_response, validate_exists
from app.core.exceptions import ClassNotFoundException, ValidationException
from app.models.class_ import (
    ClassCreate, ClassResponse, ClassUpdate,
    ClassStudentListResponse, ClassStatisticsResponse
)
from app.services.dependencies import get_class_service
from app.services.class_service import ClassService

router = APIRouter(prefix="/classes", tags=["班级管理"])

# ============================================================================
# 班级CRUD操作
# ============================================================================

@router.post("/", response_model=ClassResponse)
@handle_api_errors("创建班级")
async def create_class(
    class_: ClassCreate,
    class_service: ClassService = Depends(get_class_service)
):
    """创建班级"""
    return await class_service.create_class(class_)


@router.get("/{class_id}", response_model=ClassResponse)
@handle_api_errors("获取班级详情")
async def get_class(
    class_id: str,
    class_service: ClassService = Depends(get_class_service)
):
    """获取班级详情"""
    return await validate_exists(
        class_service.get_class,
        class_id,
        ClassNotFoundException
    )


@router.put("/{class_id}", response_model=ClassResponse)
@handle_api_errors("更新班级信息")
async def update_class(
    class_id: str,
    class_: ClassUpdate,
    class_service: ClassService = Depends(get_class_service)
):
    """更新班级信息"""
    updated = await class_service.update_class(class_id, class_)
    if not updated:
        raise ClassNotFoundException(class_id)
    return updated


@router.delete("/{class_id}")
@handle_api_errors("删除班级")
async def delete_class(
    class_id: str,
    class_service: ClassService = Depends(get_class_service)
):
    """删除班级"""
    success = await class_service.delete_class(class_id)
    if not success:
        raise ClassNotFoundException(class_id)
    return success_response("班级删除成功")


@router.get("/", response_model=List[ClassResponse])
@handle_api_errors("获取班级列表")
async def get_classes(
    skip: int = 0,
    limit: int = 100,
    class_service: ClassService = Depends(get_class_service)
):
    """获取班级列表"""
    return await class_service.get_classes(skip=skip, limit=limit)


# ============================================================================
# 班级学生管理
# ============================================================================

@router.get("/{class_id}/students", response_model=ClassStudentListResponse)
@handle_api_errors("获取班级学生列表")
async def get_class_students(
    class_id: str,
    skip: int = 0,
    limit: int = 100,
    name_filter: str = Query(None, description="按姓名过滤学生"),
    class_service: ClassService = Depends(get_class_service)
):
    """获取班级学生列表"""
    class_info = await validate_exists(
        class_service.get_class,
        class_id,
        ClassNotFoundException
    )
    
    students = await class_service.get_class_students(
        class_id=class_id,
        skip=skip,
        limit=limit,
        name_filter=name_filter
    )
    
    total = await class_service.get_class_student_count(class_id, name_filter)
    
    return {
        "class_id": class_id,
        "class_name": class_info.name,
        "students": students,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/{class_id}/students/{student_id}")
@handle_api_errors("添加学生到班级")
async def add_student_to_class(
    class_id: str,
    student_id: str,
    class_service: ClassService = Depends(get_class_service)
):
    """将学生添加到班级"""
    class_info = await validate_exists(
        class_service.get_class,
        class_id,
        ClassNotFoundException
    )
    
    success = await class_service.add_student_to_class(class_id, student_id)
    if not success:
        raise ValidationException(f"无法将学生 {student_id} 添加到班级 {class_info.name}")
    
    return success_response("学生添加到班级成功")


@router.delete("/{class_id}/students/{student_id}")
@handle_api_errors("从班级中移除学生")
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    class_service: ClassService = Depends(get_class_service)
):
    """从班级中移除学生"""
    class_info = await validate_exists(
        class_service.get_class,
        class_id,
        ClassNotFoundException
    )
    
    success = await class_service.remove_student_from_class(class_id, student_id)
    if not success:
        raise ValidationException(f"无法从班级 {class_info.name} 中移除学生 {student_id}")
    
    return success_response("学生从班级中移除成功")


# ============================================================================
# 班级统计
# ============================================================================

@router.get("/{class_id}/stats", response_model=ClassStatisticsResponse)
@handle_api_errors("获取班级统计信息")
async def get_class_stats(
    class_id: str,
    class_service: ClassService = Depends(get_class_service)
):
    """获取班级统计信息"""
    class_info = await validate_exists(
        class_service.get_class,
        class_id,
        ClassNotFoundException
    )
    
    stats = await class_service.get_class_stats(class_id)
    
    return {
        "class_id": class_id,
        "class_name": class_info.name,
        "student_count": stats["student_count"],
        "average_score": stats["average_score"],
        "top_student": stats["top_student"],
        "subject_averages": stats["subject_averages"],
        "updated_at": None
    }
