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
from app.core.logger import logger
from app.core.exceptions import FileUploadException, DatabaseException


router = APIRouter(prefix="/teacher", tags=["教师"])


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
    logger.info(f"教师 {current_user.username} 上传成绩单")
    
    try:
        # 验证文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise FileUploadException("只支持Excel文件格式（.xlsx, .xls）")
        
        # 保存上传的文件
        file_path, file_id = await upload_service.save_uploaded_file(file)
        logger.info(f"成绩文件已保存: {file_path}")
        
        # 解析Excel文件
        scores = score_service.parse_excel_file(file_path, sheet_name)
        
        if not scores:
            raise FileUploadException("未能从Excel文件中解析到有效数据")
        
        # 导入成绩数据
        imported_count = 0
        failed_count = 0
        errors = []
        
        for score_data in scores:
            try:
                # 验证数据
                if not score_service.validate_score_data(score_data):
                    failed_count += 1
                    errors.append({
                        "student_id": score_data.get("student_id", "未知"),
                        "error": "数据验证失败"
                    })
                    continue
                
                # 添加学期信息（如果提供）
                if semester:
                    score_data["semester"] = semester
                if academic_year:
                    score_data["academic_year"] = academic_year
                
                # 创建或更新学业成绩记录
                await db_service.upsert_academic_score(
                    student_id=score_data["student_id"],
                    semester=score_data.get("semester"),
                    academic_year=score_data.get("academic_year"),
                    **score_data
                )
                
                # 如果学生不存在，尝试创建学生记录
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
                        logger.info(f"自动创建学生记录: {score_data['student_id']}")
                    except Exception as e:
                        logger.warning(f"创建学生记录失败: {e}")
                
                imported_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"导入成绩失败 {score_data.get('student_id', 'unknown')}: {e}")
                errors.append({
                    "student_id": score_data.get("student_id", "未知"),
                    "error": str(e)
                })
        
        # 删除临时文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"临时文件已删除: {file_path}")
        except Exception as e:
            logger.warning(f"删除临时文件失败: {e}")
        
        return {
            "message": f"成绩单导入完成",
            "total": len(scores),
            "imported": imported_count,
            "failed": failed_count,
            "errors": errors[:10] if errors else []  # 最多返回10个错误
        }
    
    except FileUploadException as e:
        logger.error(f"上传成绩单失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"上传成绩单失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传成绩单失败: {str(e)}")


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
        # 获取成绩记录
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
        
        # 统计分析
        total_students = len(scores)
        arithmetic_averages = [s.arithmetic_average for s in scores if s.arithmetic_average > 0]
        weighted_averages = [s.weighted_average for s in scores if s.weighted_average > 0]
        gpas = [s.average_gpa for s in scores if s.average_gpa > 0]
        
        # 计算平均值
        avg_arithmetic = sum(arithmetic_averages) / len(arithmetic_averages) if arithmetic_averages else 0
        avg_weighted = sum(weighted_averages) / len(weighted_averages) if weighted_averages else 0
        avg_gpa = sum(gpas) / len(gpas) if gpas else 0
        
        # 计算最高分和最低分
        max_arithmetic = max(arithmetic_averages) if arithmetic_averages else 0
        min_arithmetic = min(arithmetic_averages) if arithmetic_averages else 0
        
        # 成绩分布（按算术平均分）
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
        
        # Top 10 学生（按算术平均分）
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
        # 获取学生信息
        student = await db_service.get_student(student_id)
        if not student:
            raise HTTPException(status_code=404, detail=f"学生不存在: {student_id}")
        
        # 获取学业成绩记录
        scores = await db_service.get_academic_scores(
            student_id=student_id,
            semester=semester,
            academic_year=academic_year
        )
        
        # 格式化返回数据
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
        # 获取学业成绩记录
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
        
        # 统计分析
        total_students = len(scores)
        arithmetic_averages = [s.arithmetic_average for s in scores if s.arithmetic_average > 0]
        weighted_averages = [s.weighted_average for s in scores if s.weighted_average > 0]
        gpas = [s.average_gpa for s in scores if s.average_gpa > 0]
        
        # 计算平均值
        avg_arithmetic = sum(arithmetic_averages) / len(arithmetic_averages) if arithmetic_averages else 0
        avg_weighted = sum(weighted_averages) / len(weighted_averages) if weighted_averages else 0
        avg_gpa = sum(gpas) / len(gpas) if gpas else 0
        
        # 计算最高分和最低分
        max_arithmetic = max(arithmetic_averages) if arithmetic_averages else 0
        min_arithmetic = min(arithmetic_averages) if arithmetic_averages else 0
        
        # 成绩分布（按算术平均分）
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
        # 获取学业成绩记录
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
        
        # 按算术平均分排序
        sorted_scores = sorted(scores, key=lambda x: x.arithmetic_average, reverse=True)
        
        # 计算排名
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
        
        # 分页处理
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
        # 获取学业成绩记录
        scores = await db_service.get_academic_scores(
            class_name=class_name,
            semester=semester,
            academic_year=academic_year
        )
        
        if not scores:
            raise HTTPException(status_code=404, detail="暂无成绩数据可导出")
        
        # 按算术平均分排序
        sorted_scores = sorted(scores, key=lambda x: x.arithmetic_average, reverse=True)
        
        # 创建Excel文件
        import pandas as pd
        import io
        import os
        from datetime import datetime
        
        # 准备数据
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
        
        # 转换为DataFrame
        df = pd.DataFrame(rankings)
        
        # 创建Excel文件
        output = io.BytesIO()
        filename = f"班级排名_{class_name or '全部'}_{semester or '全部学期'}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='排名', index=False)
        
        output.seek(0)
        
        # 返回文件
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"导出班级排名失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出班级排名失败: {str(e)}")

