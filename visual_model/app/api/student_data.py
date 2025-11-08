#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生数据API路由
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.api_utils import handle_api_errors, success_response, validate_exists
from app.core.exceptions import StudentNotFoundException
from app.models.student import (
    StudentCreate, StudentResponse, StudentUpdate,
    ActivityCreate, ActivityResponse,
    ScoreRecordCreate, ScoreRecordResponse,
    StudentAnalysisResponse
)
from app.services.dependencies import (
    get_student_service,
    get_class_service,
    get_upload_service
)
from app.services.student_service import StudentService
from app.services.class_service import ClassService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/students", tags=["学生数据"])

# ============================================================================
# 学生CRUD操作
# ============================================================================

@router.post("/", response_model=StudentResponse)
@handle_api_errors("创建学生")
async def create_student(
    student: StudentCreate,
    student_service: StudentService = Depends(get_student_service)
):
    """创建学生"""
    return await student_service.create_student(student)


@router.get("/{student_id}", response_model=StudentResponse)
@handle_api_errors("获取学生详情")
async def get_student(
    student_id: str,
    student_service: StudentService = Depends(get_student_service)
):
    """获取学生详情"""
    return await validate_exists(
        student_service.get_student, 
        student_id, 
        StudentNotFoundException
    )


@router.put("/{student_id}", response_model=StudentResponse)
@handle_api_errors("更新学生信息")
async def update_student(
    student_id: str,
    student: StudentUpdate,
    student_service: StudentService = Depends(get_student_service)
):
    """更新学生信息"""
    updated = await student_service.update_student(student_id, student)
    if not updated:
        raise StudentNotFoundException(student_id)
    return updated


@router.delete("/{student_id}")
@handle_api_errors("删除学生")
async def delete_student(
    student_id: str,
    student_service: StudentService = Depends(get_student_service)
):
    """删除学生"""
    success = await student_service.delete_student(student_id)
    if not success:
        raise StudentNotFoundException(student_id)
    return success_response("学生删除成功")


@router.get("/")
@handle_api_errors("获取学生列表")
async def get_students(
    skip: int = 0,
    limit: int = 100,
    student_service: StudentService = Depends(get_student_service)
):
    """获取学生列表"""
    students = await student_service.get_students(skip=skip, limit=limit)
    return {
        "students": students,
        "total": len(students),
        "skip": skip,
        "limit": limit
    }


# ============================================================================
# 活动管理
# ============================================================================

@router.post("/{student_id}/activities", response_model=ActivityResponse)
@handle_api_errors("创建活动")
async def create_activity(
    student_id: str,
    activity: ActivityCreate,
    student_service: StudentService = Depends(get_student_service)
):
    """为学生创建活动"""
    activity.student_id = student_id
    return await student_service.create_activity(activity)


@router.get("/{student_id}/activities", response_model=List[ActivityResponse])
@handle_api_errors("获取活动列表")
async def get_activities(
    student_id: str,
    student_service: StudentService = Depends(get_student_service)
):
    """获取学生活动列表"""
    return await student_service.get_activities(student_id)


# ============================================================================
# 分数记录
# ============================================================================

@router.post("/{student_id}/scores", response_model=ScoreRecordResponse)
@handle_api_errors("创建分数记录")
async def create_score_record(
    student_id: str,
    score: ScoreRecordCreate,
    student_service: StudentService = Depends(get_student_service)
):
    """为学生创建分数记录"""
    await validate_exists(
        student_service.get_student,
        student_id,
        StudentNotFoundException
    )
    return await student_service.create_score_record(student_id, score)


@router.get("/{student_id}/scores", response_model=List[ScoreRecordResponse])
@handle_api_errors("获取分数记录")
async def get_score_records(
    student_id: str,
    subject: Optional[str] = None,
    student_service: StudentService = Depends(get_student_service)
):
    """获取学生分数记录"""
    await validate_exists(
        student_service.get_student,
        student_id,
        StudentNotFoundException
    )
    return await student_service.get_score_records(student_id, subject)


# ============================================================================
# 学生分析
# ============================================================================

@router.get("/{student_id}/analyze", response_model=StudentAnalysisResponse)
@handle_api_errors("获取学生分析结果")
async def analyze_student_data(
    student_id: str,
    student_service: StudentService = Depends(get_student_service)
):
    """分析学生数据，直接返回分析结果"""
    student = await validate_exists(
        student_service.get_student,
        student_id,
        StudentNotFoundException
    )
    
    # 直接执行分析并返回结果
    analysis_result = await student_service.analyze_student(student_id)
    
    return analysis_result


# ============================================================================
# 班级排名
# ============================================================================

@router.get("/{student_id}/class/ranking")
@handle_api_errors("获取班级排名")
async def get_class_ranking(
    student_id: str,
    subject: Optional[str] = None,
    student_service: StudentService = Depends(get_student_service),
    class_service: ClassService = Depends(get_class_service)
):
    """获取学生在班级中的排名"""
    student = await validate_exists(
        student_service.get_student,
        student_id,
        StudentNotFoundException
    )
    
    ranking = await class_service.get_student_ranking(student_id, subject)
    if not ranking:
        from app.core.exceptions import ValidationException
        raise ValidationException(f"无法获取学生 {student_id} 的班级排名")
    
    return {
        "student_id": student_id,
        "class_name": student.class_name,
        "subject": subject,
        "ranking": ranking
    }


# ============================================================================
# 文件上传
# ============================================================================

@router.post("/{student_id}/upload")
@handle_api_errors("上传学生文件")
async def upload_student_file(
    student_id: str,
    file: UploadFile = File(...),
    student_service: StudentService = Depends(get_student_service),
    upload_service: UploadService = Depends(get_upload_service)
):
    """上传学生相关文件，直接返回上传结果"""
    await validate_exists(
        student_service.get_student,
        student_id,
        StudentNotFoundException
    )
    
    # 验证并保存文件
    upload_service.validate_image_file(file)
    file_path, file_id = await upload_service.save_uploaded_file(file)
    
    # 读取文件内容用于记录
    file.file.seek(0)
    content = await file.read()
    
    # 直接保存文件记录
    from app.services.dependencies import get_db_service
    db_service = get_db_service()
    
    await db_service.create_file(
        id=file_id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file.content_type,
        student_id=student_id
    )
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "file_size": len(content),
        "message": "文件上传成功"
    }
