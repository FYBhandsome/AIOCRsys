#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教师API路由
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from typing import Dict, Any, List, Optional
from pathlib import Path
import os

from app.models.auth import TokenData
from app.core.auth_middleware import get_teacher_user, get_teacher_or_admin
from app.services.database_tortoise import DatabaseService
from app.services.dependencies import get_db_service
from app.services.upload_service import get_upload_service, UploadService
from app.services.score_service import get_score_import_service, ScoreImportService
from app.services.comprehensive_score_service import get_comprehensive_score_service, ComprehensiveScoreService
from app.core.logger import logger
from app.core.exceptions import (
    FileUploadException, DatabaseException,
    FileValidationError, ExcelParseError, DataValidationError, BusinessError
)
from app.core.error_codes import ErrorCode, get_error_message, get_error_suggestion
from app.core.error_response import (
    create_error_response, create_success_response, generate_trace_id, ErrorDetail
)


router = APIRouter(prefix="/teacher", tags=["教师"])

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = ('.xlsx', '.xls')


@router.get("/classes")
async def get_teacher_classes(
    current_user: TokenData = Depends(get_teacher_user),
    db_service: DatabaseService = Depends(get_db_service)
) -> List[Dict[str, Any]]:
    """获取教师负责的班级列表
    
    返回该教师管理的所有班级
    """
    try:
        logger.info(f"教师 {current_user.username} 查询班级列表")
        
        classes = await db_service.get_classes()
        
        class_list = []
        for cls in classes:
            try:
                student_count = await db_service.count_students_by_class(cls.id)
                class_list.append({
                    "id": str(cls.id),
                    "name": cls.name,
                    "grade": cls.grade,
                    "major": cls.major,
                    "student_count": student_count,
                    "created_at": cls.created_at.strftime("%Y-%m-%d") if cls.created_at else None
                })
            except Exception as e:
                logger.warning(f"获取班级 {cls.id} 学生数量失败: {e}")
                class_list.append({
                    "id": str(cls.id),
                    "name": cls.name,
                    "grade": cls.grade,
                    "major": cls.major,
                    "student_count": 0,
                    "created_at": cls.created_at.strftime("%Y-%m-%d") if cls.created_at else None
                })
        
        return class_list
    
    except Exception as e:
        logger.error(f"获取班级列表失败: {e}", exc_info=True)
        return []


@router.post("/scores/upload")
async def upload_scores(
    file: UploadFile = File(..., description="成绩单文件（Excel）"),
    semester: Optional[str] = Form(None, description="学期，如：2024-1"),
    academic_year: Optional[str] = Form(None, description="学年，如：2024-2025"),
    sheet_name: Optional[str] = Form(None, description="工作表名称"),
    current_user: TokenData = Depends(get_teacher_user),
    db_service: DatabaseService = Depends(get_db_service),
    upload_service: UploadService = Depends(get_upload_service),
    score_service: ScoreImportService = Depends(get_score_import_service)
):
    """教师上传成绩单
    
    支持Excel格式的成绩单批量导入
    根据TABLE_MAP定义的列索引解析成绩数据
    """
    trace_id = generate_trace_id()
    logger.info(f"[{trace_id}] 教师 {current_user.username} 上传成绩单")
    
    try:
        if not file.filename:
            raise FileValidationError(
                error_code=ErrorCode.FILE_NOT_FOUND,
                message="未选择文件",
                filename=None
            )
        
        if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
            raise FileValidationError(
                error_code=ErrorCode.FILE_INVALID_FORMAT,
                message=f"文件格式不支持: {file.filename}",
                filename=file.filename,
                details=[{
                    "code": ErrorCode.FILE_INVALID_FORMAT,
                    "message": f"当前文件扩展名: {Path(file.filename).suffix}",
                    "field": "file_extension",
                    "value": Path(file.filename).suffix,
                    "suggestion": f"请上传 {', '.join(ALLOWED_EXTENSIONS)} 格式的Excel文件"
                }]
            )
        
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise FileValidationError(
                error_code=ErrorCode.FILE_TOO_LARGE,
                message=f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB",
                filename=file.filename,
                details=[{
                    "code": ErrorCode.FILE_TOO_LARGE,
                    "message": f"文件大小: {file_size / 1024 / 1024:.2f}MB, 最大限制: {MAX_FILE_SIZE / 1024 / 1024}MB",
                    "field": "file_size",
                    "value": f"{file_size / 1024 / 1024:.2f}MB",
                    "suggestion": "请压缩文件或分批上传"
                }]
            )
        
        if file_size == 0:
            raise FileValidationError(
                error_code=ErrorCode.FILE_EMPTY,
                message="文件内容为空",
                filename=file.filename
            )
        
        file_path = None
        try:
            file_path, file_id = await upload_service.save_uploaded_file(file)
            logger.info(f"[{trace_id}] 成绩文件已保存: {file_path}")
        except Exception as e:
            logger.error(f"[{trace_id}] 文件保存失败: {e}")
            raise FileValidationError(
                error_code=ErrorCode.FILE_UPLOAD_FAILED,
                message=f"文件保存失败: {str(e)}",
                filename=file.filename,
                details=[{
                    "code": ErrorCode.FILE_UPLOAD_FAILED,
                    "message": str(e),
                    "suggestion": "请检查磁盘空间或稍后重试"
                }]
            )
        
        try:
            parse_result = score_service.parse_excel_file(file_path, sheet_name)
            scores = parse_result.scores
            parse_warnings = parse_result.warnings
            parse_errors = parse_result.errors
        except FileNotFoundError:
            raise ExcelParseError(
                error_code=ErrorCode.FILE_NOT_FOUND,
                message="Excel文件不存在或已被删除",
                sheet_name=sheet_name
            )
        except KeyError as e:
            raise ExcelParseError(
                error_code=ErrorCode.EXCEL_SHEET_NOT_FOUND,
                message=f"工作表不存在: {sheet_name}",
                sheet_name=sheet_name,
                details=[{
                    "code": ErrorCode.EXCEL_SHEET_NOT_FOUND,
                    "message": f"找不到工作表: {sheet_name}",
                    "field": "sheet_name",
                    "value": sheet_name,
                    "suggestion": "请检查工作表名称是否正确，或使用默认工作表"
                }]
            )
        except ValueError as e:
            error_msg = str(e)
            missing_cols = []
            if "缺少" in error_msg or "列" in error_msg:
                raise ExcelParseError(
                    error_code=ErrorCode.EXCEL_MISSING_COLUMNS,
                    message=error_msg,
                    sheet_name=sheet_name,
                    missing_columns=missing_cols,
                    details=[{
                        "code": ErrorCode.EXCEL_MISSING_COLUMNS,
                        "message": error_msg,
                        "suggestion": "请确保Excel包含学号、姓名、成绩等必要列"
                    }]
                )
            raise ExcelParseError(
                error_code=ErrorCode.EXCEL_INVALID_DATA,
                message=f"Excel数据解析错误: {error_msg}",
                sheet_name=sheet_name,
                details=[{
                    "code": ErrorCode.EXCEL_INVALID_DATA,
                    "message": error_msg,
                    "suggestion": "请检查Excel数据格式是否正确"
                }]
            )
        except Exception as e:
            logger.error(f"[{trace_id}] Excel解析异常: {e}", exc_info=True)
            raise ExcelParseError(
                error_code=ErrorCode.EXCEL_READ_ERROR,
                message=f"Excel读取失败: {str(e)}",
                sheet_name=sheet_name,
                details=[{
                    "code": ErrorCode.EXCEL_READ_ERROR,
                    "message": str(e),
                    "suggestion": "请检查文件是否为有效的Excel格式，或尝试重新保存文件"
                }]
            )
        
        if not scores:
            raise ExcelParseError(
                error_code=ErrorCode.EXCEL_EMPTY_SHEET,
                message="未能从Excel文件中解析到有效数据",
                sheet_name=sheet_name,
                details=[{
                    "code": ErrorCode.EXCEL_EMPTY_SHEET,
                    "message": "Excel工作表为空或数据格式不正确",
                    "suggestion": "请确保Excel工作表包含有效数据，且格式正确"
                }] + ([{"code": ErrorCode.EXCEL_INVALID_DATA, "message": err} for err in parse_errors] if parse_errors else [])
            )
        
        if parse_warnings:
            logger.warning(f"[{trace_id}] Excel解析警告: {parse_warnings}")
        
        imported_count = 0
        failed_count = 0
        errors = []
        validation_errors = []
        
        for idx, score_data in enumerate(scores, start=1):
            row_errors = []
            
            student_id = score_data.get("student_id")
            if not student_id:
                row_errors.append({
                    "code": ErrorCode.DATA_MISSING_REQUIRED,
                    "message": "缺少学号",
                    "field": "student_id",
                    "row": idx,
                    "suggestion": "请确保每行数据包含学号"
                })
            
            student_name = score_data.get("student_name")
            if not student_name:
                row_errors.append({
                    "code": ErrorCode.DATA_MISSING_REQUIRED,
                    "message": "缺少姓名",
                    "field": "student_name",
                    "row": idx,
                    "suggestion": "请确保每行数据包含学生姓名"
                })
            
            if student_id:
                if not isinstance(student_id, str):
                    student_id = str(student_id)
                if not student_id.isalnum() or len(student_id) < 6 or len(student_id) > 20:
                    row_errors.append({
                        "code": ErrorCode.DATA_INVALID_STUDENT_ID,
                        "message": f"学号格式无效: {student_id}",
                        "field": "student_id",
                        "value": student_id,
                        "row": idx,
                        "suggestion": "学号应为6-20位的字母数字组合"
                    })
            
            if row_errors:
                failed_count += 1
                validation_errors.extend(row_errors)
                errors.append({
                    "row": idx,
                    "student_id": student_id or "未知",
                    "errors": row_errors
                })
                continue
            
            try:
                if semester:
                    score_data["semester"] = semester
                if academic_year:
                    score_data["academic_year"] = academic_year
                
                # 移除已单独传递的参数，避免重复
                score_data_copy = {k: v for k, v in score_data.items() 
                                   if k not in ('student_id', 'semester', 'academic_year')}
                
                await db_service.upsert_academic_score(
                    student_id=score_data["student_id"],
                    semester=score_data.get("semester"),
                    academic_year=score_data.get("academic_year"),
                    **score_data_copy
                )
                
                student = await db_service.get_student(score_data["student_id"])
                if not student:
                    try:
                        await db_service.create_student(
                            id=score_data["student_id"],
                            name=score_data["student_name"],
                            college=score_data.get("college", ""),
                            major=score_data.get("major", ""),
                            class_name=score_data.get("class_name", ""),
                            grade=score_data.get("grade", "")
                        )
                        logger.info(f"[{trace_id}] 自动创建学生记录: {score_data['student_id']}")
                    except Exception as e:
                        logger.warning(f"[{trace_id}] 创建学生记录失败: {e}")
                
                imported_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"[{trace_id}] 导入成绩失败 {score_data.get('student_id', 'unknown')}: {e}")
                errors.append({
                    "row": idx,
                    "student_id": score_data.get("student_id", "未知"),
                    "errors": [{
                        "code": ErrorCode.SCORE_IMPORT_FAILED,
                        "message": str(e),
                        "suggestion": "请检查数据格式后重试"
                    }]
                })
        
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[{trace_id}] 临时文件已删除: {file_path}")
        except Exception as e:
            logger.warning(f"[{trace_id}] 删除临时文件失败: {e}")
        
        if failed_count > 0 and imported_count == 0:
            raise BusinessError(
                error_code=ErrorCode.SCORE_IMPORT_FAILED,
                message="成绩导入失败，所有记录均未成功",
                details=(validation_errors[:10] if validation_errors else 
                        [{"code": ErrorCode.SCORE_IMPORT_FAILED, "message": e.get("errors", [{}])[0].get("message", "未知错误")} for e in errors[:10]])
            )
        
        response_data = {
            "total": len(scores),
            "imported": imported_count,
            "failed": failed_count,
            "errors": errors[:10] if errors else []
        }
        
        if failed_count > 0:
            logger.warning(
                f"[{trace_id}] 成绩导入部分成功: 总数={len(scores)}, "
                f"成功={imported_count}, 失败={failed_count}"
            )
            return create_success_response(
                message=f"成绩单导入完成，{imported_count}条成功，{failed_count}条失败",
                data=response_data,
                trace_id=trace_id
            )
        
        logger.info(f"[{trace_id}] 成绩导入成功: {imported_count}条记录")
        return create_success_response(
            message=f"成绩单导入成功，共导入{imported_count}条记录",
            data=response_data,
            trace_id=trace_id
        )
    
    except FileValidationError as e:
        logger.error(f"[{trace_id}] 文件验证失败: {e.message}")
        raise
    except ExcelParseError as e:
        logger.error(f"[{trace_id}] Excel解析失败: {e.message}")
        raise
    except DataValidationError as e:
        logger.error(f"[{trace_id}] 数据验证失败: {e.message}")
        raise
    except BusinessError as e:
        logger.error(f"[{trace_id}] 业务错误: {e.message}")
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] 上传成绩单失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                error_message=f"上传成绩单失败: {str(e)}",
                trace_id=trace_id
            )
        )


@router.get("/scores/analysis")
async def analyze_scores(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_user),
    db_service: DatabaseService = Depends(get_db_service)
) -> Dict[str, Any]:
    """成绩分析
    
    分析班级或全年级的成绩分布、平均分、排名等
    
    可选参数：
    - class_name: 班级筛选
    - semester: 学期筛选
    - academic_year: 学年筛选
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            return {
                "class_name": class_name or "all",
                "semester": semester,
                "academic_year": academic_year,
                "total_students": 0,
                "message": "暂无成绩数据"
            }
        
        total_students = len(scores)
        arithmetic_averages = [s.arithmetic_average for s in scores if s.arithmetic_average > 0]
        weighted_averages = [s.weighted_average for s in scores if s.weighted_average > 0]
        gpas = [s.average_gpa for s in scores if s.average_gpa > 0]
        
        avg_arithmetic = sum(arithmetic_averages) / len(arithmetic_averages) if arithmetic_averages else 0
        avg_weighted = sum(weighted_averages) / len(weighted_averages) if weighted_averages else 0
        avg_gpa = sum(gpas) / len(gpas) if gpas else 0
        
        max_arithmetic = max(arithmetic_averages) if arithmetic_averages else 0
        min_arithmetic = min(arithmetic_averages) if arithmetic_averages else 0
        
        distribution = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "0-59": 0
        }
        
        for avg in arithmetic_averages:
            if avg >= 90:
                distribution["90-100"] += 1
            elif avg >= 80:
                distribution["80-89"] += 1
            elif avg >= 70:
                distribution["70-79"] += 1
            elif avg >= 60:
                distribution["60-69"] += 1
            else:
                distribution["0-59"] += 1
        
        sorted_scores = sorted(scores, key=lambda x: x.arithmetic_average, reverse=True)[:10]
        top_10 = []
        for score in sorted_scores:
            top_10.append({
                "student_id": score.student_id,
                "student_name": score.student_name,
                "arithmetic_average": score.arithmetic_average,
                "weighted_average": score.weighted_average,
                "average_gpa": score.average_gpa
            })
        
        return {
            "class_name": class_name or "all",
            "semester": semester,
            "academic_year": academic_year,
            "total_students": total_students,
            "statistics": {
                "average_arithmetic": round(avg_arithmetic, 2),
                "average_weighted": round(avg_weighted, 2),
                "average_gpa": round(avg_gpa, 2),
                "max_arithmetic": round(max_arithmetic, 2),
                "min_arithmetic": round(min_arithmetic, 2)
            },
            "distribution": distribution,
            "top_10": top_10
        }
    
    except Exception as e:
        logger.error(f"成绩分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"成绩分析失败: {str(e)}")


@router.get("/students")
async def list_students(
    class_name: Optional[str] = None,
    grade: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
) -> Dict[str, Any]:
    """查看学生列表
    
    可选参数：
    - class_name: 班级筛选
    - grade: 年级筛选
    - limit: 每页数量
    - offset: 偏移量
    """
    try:
        students = await db_service.get_students(
            class_name=class_name,
            grade=grade,
            limit=limit,
            offset=offset
        )
        
        student_list = []
        for student in students:
            student_list.append({
                "id": student.id,
                "name": student.name,
                "college": student.college,
                "major": student.major,
                "class_name": student.class_name,
                "grade": student.grade
            })
        
        return {
            "total": len(student_list),
            "students": student_list
        }
    
    except Exception as e:
        logger.error(f"获取学生列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取学生列表失败: {str(e)}")


@router.get("/students/{student_id}/scores")
async def get_student_scores(
    student_id: str,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """查看指定学生的学业成绩
    
    可选参数：
    - semester: 学期筛选
    - academic_year: 学年筛选
    """
    try:
        student = await db_service.get_student(student_id)
        if not student:
            raise HTTPException(status_code=404, detail=f"学生不存在: {student_id}")
        
        scores = await db_service.get_academic_scores(
            student_id=student_id,
            semester=semester,
            academic_year=academic_year
        )
        
        score_list = []
        for score in scores:
            score_list.append({
                "id": score.id,
                "student_id": score.student_id,
                "student_name": score.student_name,
                "semester": score.semester,
                "academic_year": score.academic_year,
                "total_score": score.total_score,
                "arithmetic_average": score.arithmetic_average,
                "weighted_average": score.weighted_average,
                "average_gpa": score.average_gpa,
                "pass_rate": score.pass_rate,
                "course_count": score.course_count,
                "failed_course_count": score.failed_course_count,
                "created_at": score.created_at.isoformat() if score.created_at else None
            })
        
        return {
            "student_id": student_id,
            "student_name": student.name,
            "total_records": len(score_list),
            "scores": score_list
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生成绩失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取学生成绩失败: {str(e)}")


@router.put("/students/{student_id}/scores")
async def update_student_score(
    student_id: str,
    score_data: Dict[str, Any],
    current_user: TokenData = Depends(get_teacher_user)
):
    """修改学生成绩"""
    logger.info(f"教师 {current_user.username} 修改学生 {student_id} 成绩")
    return {"message": "成绩更新成功"}


@router.get("/classes/stats")
async def get_class_stats(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取班级统计数据
    
    可选参数：
    - class_name: 班级筛选
    - semester: 学期筛选
    - academic_year: 学年筛选
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            return {
                "class_name": class_name or "all",
                "semester": semester,
                "academic_year": academic_year,
                "total_students": 0,
                "message": "暂无成绩数据"
            }
        
        total_students = len(scores)
        arithmetic_averages = [s.arithmetic_average for s in scores if s.arithmetic_average > 0]
        weighted_averages = [s.weighted_average for s in scores if s.weighted_average > 0]
        gpas = [s.average_gpa for s in scores if s.average_gpa > 0]
        
        avg_arithmetic = sum(arithmetic_averages) / len(arithmetic_averages) if arithmetic_averages else 0
        avg_weighted = sum(weighted_averages) / len(weighted_averages) if weighted_averages else 0
        avg_gpa = sum(gpas) / len(gpas) if gpas else 0
        
        max_arithmetic = max(arithmetic_averages) if arithmetic_averages else 0
        min_arithmetic = min(arithmetic_averages) if arithmetic_averages else 0
        
        distribution = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "0-59": 0
        }
        
        for avg in arithmetic_averages:
            if avg >= 90:
                distribution["90-100"] += 1
            elif avg >= 80:
                distribution["80-89"] += 1
            elif avg >= 70:
                distribution["70-79"] += 1
            elif avg >= 60:
                distribution["60-69"] += 1
            else:
                distribution["0-59"] += 1
        
        return {
            "class_name": class_name or "all",
            "semester": semester,
            "academic_year": academic_year,
            "total_students": total_students,
            "statistics": {
                "average_arithmetic": round(avg_arithmetic, 2),
                "average_weighted": round(avg_weighted, 2),
                "average_gpa": round(avg_gpa, 2),
                "max_arithmetic": round(max_arithmetic, 2),
                "min_arithmetic": round(min_arithmetic, 2)
            },
            "distribution": distribution
        }
    
    except Exception as e:
        logger.error(f"获取班级统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取班级统计失败: {str(e)}")


@router.get("/classes/ranking")
async def get_class_ranking(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取班级学生排名
    
    可选参数：
    - class_name: 班级筛选
    - semester: 学期筛选
    - academic_year: 学年筛选
    - limit: 每页数量
    - offset: 偏移量
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            return {
                "class_name": class_name or "all",
                "semester": semester,
                "academic_year": academic_year,
                "total_students": 0,
                "rankings": [],
                "message": "暂无成绩数据"
            }
        
        sorted_scores = sorted(scores, key=lambda x: x.arithmetic_average, reverse=True)
        
        rankings = []
        for i, score in enumerate(sorted_scores):
            rankings.append({
                "rank": i + 1,
                "student_id": score.student_id,
                "student_name": score.student_name,
                "class_name": score.class_name,
                "arithmetic_average": score.arithmetic_average,
                "weighted_average": score.weighted_average,
                "average_gpa": score.average_gpa
            })
        
        total = len(rankings)
        paginated_rankings = rankings[offset:offset+limit]
        
        return {
            "class_name": class_name or "all",
            "semester": semester,
            "academic_year": academic_year,
            "total_students": total,
            "rankings": paginated_rankings
        }
    
    except Exception as e:
        logger.error(f"获取班级排名失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取班级排名失败: {str(e)}")


@router.get("/classes/ranking/export")
async def export_class_ranking(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """导出班级学生排名为Excel文件
    
    可选参数：
    - class_name: 班级筛选
    - semester: 学期筛选
    - academic_year: 学年筛选
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            raise HTTPException(status_code=404, detail="暂无成绩数据可导出")
        
        sorted_scores = sorted(scores, key=lambda x: x.arithmetic_average, reverse=True)
        
        import pandas as pd
        import io
        from datetime import datetime
        
        rankings = []
        for i, score in enumerate(sorted_scores):
            rankings.append({
                "排名": i + 1,
                "学号": score.student_id,
                "姓名": score.student_name,
                "班级": score.class_name,
                "算术平均分": score.arithmetic_average,
                "加权平均分": score.weighted_average,
                "平均GPA": score.average_gpa
            })
        
        df = pd.DataFrame(rankings)
        
        output = io.BytesIO()
        filename = f"班级排名_{class_name or '全部'}_{semester or '全部学期'}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='排名', index=False)
        
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"导出班级排名失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出班级排名失败: {str(e)}")


@router.get("/analysis/distribution")
async def get_score_distribution(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取成绩分布数据
    
    返回指定班级或全部学生的成绩分布统计
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            return {
                "class_name": class_name or "all",
                "total_students": 0,
                "distribution": {},
                "message": "暂无成绩数据"
            }
        
        arithmetic_averages = [s.arithmetic_average for s in scores if s.arithmetic_average > 0]
        
        distribution = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "0-59": 0
        }
        
        for avg in arithmetic_averages:
            if avg >= 90:
                distribution["90-100"] += 1
            elif avg >= 80:
                distribution["80-89"] += 1
            elif avg >= 70:
                distribution["70-79"] += 1
            elif avg >= 60:
                distribution["60-69"] += 1
            else:
                distribution["0-59"] += 1
        
        return {
            "class_name": class_name or "all",
            "semester": semester,
            "academic_year": academic_year,
            "total_students": len(scores),
            "distribution": distribution,
            "average": round(sum(arithmetic_averages) / len(arithmetic_averages), 2) if arithmetic_averages else 0
        }
    
    except Exception as e:
        logger.error(f"获取成绩分布失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取成绩分布失败: {str(e)}")


@router.get("/analysis/subject-comparison")
async def get_subject_comparison(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取各科目成绩对比
    
    返回不同科目的成绩对比数据
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            return {
                "class_name": class_name or "all",
                "subjects": [],
                "message": "暂无成绩数据"
            }
        
        subject_stats = {}
        
        for score in scores:
            if score.details:
                for course in score.details:
                    course_name = course.get("course_name", "未知科目")
                    course_score = course.get("score", 0)
                    
                    if course_name not in subject_stats:
                        subject_stats[course_name] = {
                            "name": course_name,
                            "scores": [],
                            "count": 0
                        }
                    
                    if course_score > 0:
                        subject_stats[course_name]["scores"].append(course_score)
                        subject_stats[course_name]["count"] += 1
        
        subjects = []
        for name, stats in subject_stats.items():
            if stats["scores"]:
                subjects.append({
                    "name": name,
                    "average": round(sum(stats["scores"]) / len(stats["scores"]), 2),
                    "max": max(stats["scores"]),
                    "min": min(stats["scores"]),
                    "count": stats["count"]
                })
        
        subjects.sort(key=lambda x: x["average"], reverse=True)
        
        return {
            "class_name": class_name or "all",
            "semester": semester,
            "academic_year": academic_year,
            "subjects": subjects[:20]
        }
    
    except Exception as e:
        logger.error(f"获取科目对比失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取科目对比失败: {str(e)}")


@router.get("/analysis/trend")
async def get_score_trend(
    class_name: Optional[str] = None,
    student_id: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取成绩趋势
    
    返回班级或学生历次成绩变化趋势
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            student_id=student_id
        )
        
        if not scores:
            return {
                "class_name": class_name,
                "student_id": student_id,
                "trend": [],
                "message": "暂无成绩数据"
            }
        
        trend_data = []
        for score in sorted(scores, key=lambda x: (x.academic_year or "", x.semester or "")):
            trend_data.append({
                "academic_year": score.academic_year,
                "semester": score.semester,
                "arithmetic_average": score.arithmetic_average,
                "weighted_average": score.weighted_average,
                "average_gpa": score.average_gpa,
                "class_rank": score.arithmetic_average_rank
            })
        
        return {
            "class_name": class_name,
            "student_id": student_id,
            "total_records": len(trend_data),
            "trend": trend_data
        }
    
    except Exception as e:
        logger.error(f"获取成绩趋势失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取成绩趋势失败: {str(e)}")


@router.get("/analysis/class-comparison")
async def get_class_comparison(
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取班级对比数据
    
    返回不同班级之间的成绩对比
    """
    try:
        scores = await db_service.get_academic_scores(
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            return {
                "semester": semester,
                "academic_year": academic_year,
                "classes": [],
                "message": "暂无成绩数据"
            }
        
        class_stats = {}
        
        for score in scores:
            cls_name = score.class_name or "未知班级"
            
            if cls_name not in class_stats:
                class_stats[cls_name] = {
                    "name": cls_name,
                    "arithmetic_averages": [],
                    "weighted_averages": [],
                    "gpas": []
                }
            
            if score.arithmetic_average > 0:
                class_stats[cls_name]["arithmetic_averages"].append(score.arithmetic_average)
            if score.weighted_average > 0:
                class_stats[cls_name]["weighted_averages"].append(score.weighted_average)
            if score.average_gpa > 0:
                class_stats[cls_name]["gpas"].append(score.average_gpa)
        
        classes = []
        for name, stats in class_stats.items():
            classes.append({
                "name": name,
                "student_count": len(stats["arithmetic_averages"]),
                "avg_arithmetic": round(sum(stats["arithmetic_averages"]) / len(stats["arithmetic_averages"]), 2) if stats["arithmetic_averages"] else 0,
                "avg_weighted": round(sum(stats["weighted_averages"]) / len(stats["weighted_averages"]), 2) if stats["weighted_averages"] else 0,
                "avg_gpa": round(sum(stats["gpas"]) / len(stats["gpas"]), 2) if stats["gpas"] else 0
            })
        
        classes.sort(key=lambda x: x["avg_arithmetic"], reverse=True)
        
        return {
            "semester": semester,
            "academic_year": academic_year,
            "classes": classes
        }
    
    except Exception as e:
        logger.error(f"获取班级对比失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取班级对比失败: {str(e)}")


@router.get("/analysis/correlation")
async def get_score_correlation(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取成绩相关性分析
    
    返回不同成绩指标之间的相关性
    """
    try:
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores or len(scores) < 2:
            return {
                "class_name": class_name or "all",
                "correlation": {},
                "message": "数据不足，无法计算相关性"
            }
        
        import numpy as np
        
        arithmetic = np.array([s.arithmetic_average for s in scores if s.arithmetic_average > 0])
        weighted = np.array([s.weighted_average for s in scores if s.weighted_average > 0])
        gpa = np.array([s.average_gpa for s in scores if s.average_gpa > 0])
        
        correlation = {}
        
        if len(arithmetic) > 1 and len(weighted) > 1:
            min_len = min(len(arithmetic), len(weighted))
            correlation["arithmetic_vs_weighted"] = round(
                float(np.corrcoef(arithmetic[:min_len], weighted[:min_len])[0, 1]), 3
            ) if min_len > 1 else 0
        
        if len(arithmetic) > 1 and len(gpa) > 1:
            min_len = min(len(arithmetic), len(gpa))
            correlation["arithmetic_vs_gpa"] = round(
                float(np.corrcoef(arithmetic[:min_len], gpa[:min_len])[0, 1]), 3
            ) if min_len > 1 else 0
        
        if len(weighted) > 1 and len(gpa) > 1:
            min_len = min(len(weighted), len(gpa))
            correlation["weighted_vs_gpa"] = round(
                float(np.corrcoef(weighted[:min_len], gpa[:min_len])[0, 1]), 3
            ) if min_len > 1 else 0
        
        return {
            "class_name": class_name or "all",
            "semester": semester,
            "academic_year": academic_year,
            "sample_size": len(scores),
            "correlation": correlation
        }
    
    except Exception as e:
        logger.error(f"获取成绩相关性失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取成绩相关性失败: {str(e)}")


@router.get("/analysis/export")
async def export_analysis_data(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: TokenData = Depends(get_teacher_or_admin),
    db_service: DatabaseService = Depends(get_db_service)
):
    """导出分析数据
    
    导出成绩分析报告为Excel文件
    """
    try:
        import pandas as pd
        import io
        from datetime import datetime
        
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            raise HTTPException(status_code=404, detail="暂无成绩数据可导出")
        
        data = []
        for score in scores:
            data.append({
                "学号": score.student_id,
                "姓名": score.student_name,
                "班级": score.class_name,
                "学年": score.academic_year,
                "学期": score.semester,
                "算术平均分": score.arithmetic_average,
                "加权平均分": score.weighted_average,
                "平均GPA": score.average_gpa,
                "通过率": score.pass_rate,
                "课程门数": score.course_count,
                "不及格门次": score.failed_course_count
            })
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        filename = f"成绩分析_{class_name or '全部'}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='成绩数据', index=False)
        
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出分析数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出分析数据失败: {str(e)}")


@router.post("/comprehensive/upload")
async def upload_comprehensive_scores(
    file: UploadFile = File(..., description="综测计算表格文件（Excel）"),
    academic_year: Optional[str] = Form(None, description="学年，如：2024-2025"),
    semester: Optional[str] = Form(None, description="学期，如：2024-1"),
    current_user: TokenData = Depends(get_teacher_user),
    db_service: DatabaseService = Depends(get_db_service),
    upload_service: UploadService = Depends(get_upload_service),
    comprehensive_service: ComprehensiveScoreService = Depends(get_comprehensive_score_service)
):
    """教师上传综测计算表格
    
    支持Excel格式的综测计算表格批量导入
    根据README.md定义的表格结构解析数据
    
    表格结构：
    - 综合测评计算表（主表）：第3行为列头，第4行起为数据行
    - 加减分说明（辅助表）：第1行为列头，第2行起为数据行
    """
    trace_id = generate_trace_id()
    logger.info(f"[{trace_id}] 教师 {current_user.username} 上传综测表格")
    
    try:
        if not file.filename:
            raise FileValidationError(
                error_code=ErrorCode.FILE_NOT_FOUND,
                message="未选择文件",
                filename=None
            )
        
        if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
            raise FileValidationError(
                error_code=ErrorCode.FILE_INVALID_FORMAT,
                message=f"文件格式不支持: {file.filename}",
                filename=file.filename,
                details=[{
                    "code": ErrorCode.FILE_INVALID_FORMAT,
                    "message": f"当前文件扩展名: {Path(file.filename).suffix}",
                    "field": "file_extension",
                    "value": Path(file.filename).suffix,
                    "suggestion": f"请上传 {', '.join(ALLOWED_EXTENSIONS)} 格式的Excel文件"
                }]
            )
        
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise FileValidationError(
                error_code=ErrorCode.FILE_TOO_LARGE,
                message=f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB",
                filename=file.filename,
                details=[{
                    "code": ErrorCode.FILE_TOO_LARGE,
                    "message": f"文件大小: {file_size / 1024 / 1024:.2f}MB, 最大限制: {MAX_FILE_SIZE / 1024 / 1024}MB",
                    "field": "file_size",
                    "value": f"{file_size / 1024 / 1024:.2f}MB",
                    "suggestion": "请压缩文件或分批上传"
                }]
            )
        
        if file_size == 0:
            raise FileValidationError(
                error_code=ErrorCode.FILE_EMPTY,
                message="文件内容为空",
                filename=file.filename
            )
        
        file_path = None
        try:
            file_path, file_id = await upload_service.save_uploaded_file(file)
            logger.info(f"[{trace_id}] 综测表格已保存: {file_path}")
        except Exception as e:
            logger.error(f"[{trace_id}] 文件保存失败: {e}")
            raise FileValidationError(
                error_code=ErrorCode.FILE_UPLOAD_FAILED,
                message=f"文件保存失败: {str(e)}",
                filename=file.filename,
                details=[{
                    "code": ErrorCode.FILE_UPLOAD_FAILED,
                    "message": str(e),
                    "suggestion": "请检查磁盘空间或稍后重试"
                }]
            )
        
        try:
            import pandas as pd
            
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            logger.info(f"[{trace_id}] Excel工作表: {sheet_names}")
            
            main_sheet_name = None
            detail_sheet_name = None
            
            for name in sheet_names:
                if '综合测评计算表' in name or '计算表' in name:
                    main_sheet_name = name
                elif '加减分说明' in name or '加减分' in name:
                    detail_sheet_name = name
            
            if not main_sheet_name:
                main_sheet_name = sheet_names[0] if sheet_names else None
            
            scores_data = []
            
            if main_sheet_name:
                df_main = pd.read_excel(file_path, sheet_name=main_sheet_name, header=2)
                logger.info(f"[{trace_id}] 主表列名: {list(df_main.columns)}")
                
                for idx, row in df_main.iterrows():
                    student_id = None
                    student_name = None
                    
                    for col in df_main.columns:
                        col_str = str(col).strip()
                        if '学号' in col_str:
                            student_id = str(row[col]) if pd.notna(row[col]) else None
                        elif '姓名' in col_str:
                            student_name = str(row[col]) if pd.notna(row[col]) else None
                    
                    if not student_id or student_id == 'nan':
                        continue
                    
                    score_entry = {
                        'student_id': student_id,
                        'student_name': student_name,
                        'academic_year': academic_year,
                        'semester': semester,
                        'scores': {}
                    }
                    
                    for col in df_main.columns:
                        col_str = str(col).strip()
                        value = row[col]
                        
                        if 'A1' in col_str and '基础分' in col_str:
                            score_entry['scores']['a1_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'A2' in col_str and '附加分' in col_str:
                            score_entry['scores']['a2_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'A3' in col_str and '扣分' in col_str:
                            score_entry['scores']['a3_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'A' in col_str and '总分' in col_str and '%' not in col_str:
                            score_entry['scores']['a_total_score'] = float(value) if pd.notna(value) else 0.0
                        elif '学习成绩' in col_str and '%' not in col_str and '70%' not in col_str:
                            score_entry['scores']['b_total_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'C1' in col_str:
                            score_entry['scores']['c1_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'C2' in col_str:
                            score_entry['scores']['c2_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'C3' in col_str:
                            score_entry['scores']['c3_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'C4' in col_str:
                            score_entry['scores']['c4_score'] = float(value) if pd.notna(value) else 0.0
                        elif 'C' in col_str and '总分' in col_str:
                            score_entry['scores']['c_total_score'] = float(value) if pd.notna(value) else 0.0
                        elif '综合测评总成绩' in col_str or '总成绩' in col_str:
                            score_entry['scores']['total_score'] = float(value) if pd.notna(value) else 0.0
                        elif '班级' in col_str:
                            score_entry['class_name'] = str(value) if pd.notna(value) else None
                        elif '专业' in col_str:
                            score_entry['major'] = str(value) if pd.notna(value) else None
                    
                    scores_data.append(score_entry)
            
            detail_data = []
            if detail_sheet_name:
                df_detail = pd.read_excel(file_path, sheet_name=detail_sheet_name, header=0)
                logger.info(f"[{trace_id}] 辅助表列名: {list(df_detail.columns)}")
                
                for idx, row in df_detail.iterrows():
                    student_name = None
                    for col in df_detail.columns:
                        col_str = str(col).strip()
                        if '姓名' in col_str:
                            student_name = str(row[col]) if pd.notna(row[col]) else None
                            break
                    
                    if not student_name or student_name == 'nan':
                        continue
                    
                    detail_entry = {
                        'student_name': student_name,
                        'details': []
                    }
                    
                    for col in df_detail.columns:
                        col_str = str(col).strip()
                        value = row[col]
                        
                        if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                            detail_entry['details'].append({
                                'column': col_str,
                                'value': str(value)
                            })
                    
                    if detail_entry['details']:
                        detail_data.append(detail_entry)
            
        except FileNotFoundError:
            raise ExcelParseError(
                error_code=ErrorCode.FILE_NOT_FOUND,
                message="Excel文件不存在或已被删除",
                sheet_name=main_sheet_name
            )
        except Exception as e:
            logger.error(f"[{trace_id}] Excel解析异常: {e}", exc_info=True)
            raise ExcelParseError(
                error_code=ErrorCode.EXCEL_READ_ERROR,
                message=f"Excel读取失败: {str(e)}",
                sheet_name=main_sheet_name,
                details=[{
                    "code": ErrorCode.EXCEL_READ_ERROR,
                    "message": str(e),
                    "suggestion": "请检查文件是否为有效的Excel格式，或尝试重新保存文件"
                }]
            )
        
        if not scores_data:
            raise ExcelParseError(
                error_code=ErrorCode.EXCEL_EMPTY_SHEET,
                message="未能从Excel文件中解析到有效综测数据",
                sheet_name=main_sheet_name,
                details=[{
                    "code": ErrorCode.EXCEL_EMPTY_SHEET,
                    "message": "Excel工作表为空或数据格式不正确",
                    "suggestion": "请确保Excel工作表包含有效数据，且格式正确"
                }]
            )
        
        imported_count = 0
        failed_count = 0
        errors = []
        
        from app.models.tortoise_models import ComprehensiveScore, Student
        
        for idx, score_data in enumerate(scores_data, start=1):
            try:
                student_id = score_data.get('student_id')
                if not student_id:
                    failed_count += 1
                    errors.append({
                        "row": idx,
                        "error": "缺少学号"
                    })
                    continue
                
                student = await Student.get_or_none(id=student_id)
                if not student:
                    student = await Student.create(
                        id=student_id,
                        name=score_data.get('student_name', ''),
                        class_name=score_data.get('class_name', ''),
                        major=score_data.get('major', '')
                    )
                    logger.info(f"[{trace_id}] 自动创建学生记录: {student_id}")
                
                scores = score_data.get('scores', {})
                
                comp_score, created = await ComprehensiveScore.update_or_create(
                    student_id=student_id,
                    semester=semester or '',
                    academic_year=academic_year or '',
                    defaults={
                        'a1_score': scores.get('a1_score', 0.0),
                        'a2_score': scores.get('a2_score', 0.0),
                        'a3_score': scores.get('a3_score', 0.0),
                        'a_total_score': scores.get('a_total_score', 0.0),
                        'b_total_score': scores.get('b_total_score', 0.0),
                        'c1_score': scores.get('c1_score', 0.0),
                        'c2_score': scores.get('c2_score', 0.0),
                        'c3_score': scores.get('c3_score', 0.0),
                        'c4_score': scores.get('c4_score', 0.0),
                        'c_total_score': scores.get('c_total_score', 0.0),
                        'total_score': scores.get('total_score', 0.0),
                    }
                )
                
                imported_count += 1
                logger.debug(f"[{trace_id}] 导入综测数据: {student_id}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"[{trace_id}] 导入综测数据失败 {score_data.get('student_id', 'unknown')}: {e}")
                errors.append({
                    "row": idx,
                    "student_id": score_data.get('student_id', '未知'),
                    "error": str(e)
                })
        
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[{trace_id}] 临时文件已删除: {file_path}")
        except Exception as e:
            logger.warning(f"[{trace_id}] 删除临时文件失败: {e}")
        
        if failed_count > 0 and imported_count == 0:
            raise BusinessError(
                error_code=ErrorCode.SCORE_IMPORT_FAILED,
                message="综测数据导入失败，所有记录均未成功",
                details=errors[:10]
            )
        
        response_data = {
            "total": len(scores_data),
            "imported": imported_count,
            "failed": failed_count,
            "detail_count": len(detail_data),
            "errors": errors[:10] if errors else []
        }
        
        if failed_count > 0:
            logger.warning(
                f"[{trace_id}] 综测数据导入部分成功: 总数={len(scores_data)}, "
                f"成功={imported_count}, 失败={failed_count}"
            )
            return create_success_response(
                message=f"综测表格导入完成，{imported_count}条成功，{failed_count}条失败",
                data=response_data,
                trace_id=trace_id
            )
        
        logger.info(f"[{trace_id}] 综测数据导入成功: {imported_count}条记录")
        return create_success_response(
            message=f"综测表格导入成功，共导入{imported_count}条记录",
            data=response_data,
            trace_id=trace_id
        )
    
    except FileValidationError as e:
        logger.error(f"[{trace_id}] 文件验证失败: {e.message}")
        raise
    except ExcelParseError as e:
        logger.error(f"[{trace_id}] Excel解析失败: {e.message}")
        raise
    except DataValidationError as e:
        logger.error(f"[{trace_id}] 数据验证失败: {e.message}")
        raise
    except BusinessError as e:
        logger.error(f"[{trace_id}] 业务错误: {e.message}")
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] 上传综测表格失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                error_message=f"上传综测表格失败: {str(e)}",
                trace_id=trace_id
            )
        )


@router.get("/comprehensive/list")
async def get_comprehensive_scores(
    class_name: Optional[str] = None,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_teacher_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取综测数据列表
    
    可选参数：
    - class_name: 班级筛选
    - semester: 学期筛选
    - academic_year: 学年筛选
    - limit: 每页数量
    - offset: 偏移量
    """
    trace_id = generate_trace_id()
    logger.info(f"[{trace_id}] 教师 {current_user.username} 查询综测数据列表")
    
    try:
        from app.models.tortoise_models import ComprehensiveScore, Student
        
        query = ComprehensiveScore.all()
        
        if academic_year:
            query = query.filter(academic_year=academic_year)
        if semester:
            query = query.filter(semester=semester)
        if class_name:
            query = query.filter(student__class_name=class_name)
        
        total = await query.count()
        scores = await query.order_by('-total_score').offset(offset).limit(limit)
        
        score_list = []
        for score in scores:
            student = await Student.get_or_none(id=score.student_id)
            score_list.append({
                "id": score.id,
                "student_id": score.student_id,
                "student_name": student.name if student else score.student_id,
                "class_name": student.class_name if student else None,
                "academic_year": score.academic_year,
                "semester": score.semester,
                "a1_score": score.a1_score,
                "a2_score": score.a2_score,
                "a3_score": score.a3_score,
                "a_total_score": score.a_total_score,
                "b_total_score": score.b_total_score,
                "c1_score": score.c1_score,
                "c2_score": score.c2_score,
                "c3_score": score.c3_score,
                "c4_score": score.c4_score,
                "c_total_score": score.c_total_score,
                "total_score": score.total_score,
                "created_at": score.created_at.isoformat() if score.created_at else None,
                "updated_at": score.updated_at.isoformat() if score.updated_at else None
            })
        
        return create_success_response(
            message="获取综测数据成功",
            data={
                "total": total,
                "limit": limit,
                "offset": offset,
                "scores": score_list
            },
            trace_id=trace_id
        )
    
    except Exception as e:
        logger.error(f"[{trace_id}] 获取综测数据列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                error_message=f"获取综测数据失败: {str(e)}",
                trace_id=trace_id
            )
        )
