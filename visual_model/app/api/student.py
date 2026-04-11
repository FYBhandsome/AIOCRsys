#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生API路由
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Dict, Any, List
import asyncio
from datetime import datetime

from app.models.auth import TokenData
from app.models.upload import OCRResult
from app.core.auth_middleware import get_student_user
from app.services.ocr_service import get_ocr_service
from app.services.upload_service import get_upload_service, UploadService
from app.services.database_tortoise import DatabaseService
from app.services.dependencies import get_db_service
from app.services.rag_client import get_rag_client
from app.core.executor_manager import get_executor
from app.core.logger import logger
from config import settings


router = APIRouter(prefix="/student", tags=["学生"])


@router.post("/certificate/upload")
async def upload_certificate(
    file: UploadFile = File(..., description="获奖证书图片"),
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service),
    upload_service: UploadService = Depends(get_upload_service)
) -> Dict[str, Any]:
    """学生上传获奖证书
    
    上传证书图片并进行OCR识别，自动计算综测加分
    
    返回结果包含:
    - 上传结果
    - OCR识别结果
    - RAG检索到的规则信息
    - 加分结果
    """
    try:
        upload_service.validate_image_file(file)
        
        file_path, file_id = await upload_service.save_uploaded_file(file)
        
        file.file.seek(0)
        file_content = await file.read()
        file_size = len(file_content)
        
        await db_service.create_file(
            id=file_id,
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            file_path=file_path,
            student_id=current_user.user_id
        )
        
        ocr_service = get_ocr_service()
        executor = get_executor()
        
        recognition_results = await asyncio.get_event_loop().run_in_executor(
            executor,
            ocr_service.recognize_text,
            file_path,
            None
        )
        
        certificate_info = ocr_service.extract_certificate_info(
            image_path=file_path,
            ocr_results=recognition_results
        )
        
        from app.services.certificate_service import get_certificate_service
        cert_service = get_certificate_service()
        
        cert_text = certificate_info.get("raw_text", "")
        if not cert_text:
            cert_text = " ".join([item.get("text", "") for item in recognition_results])

        # OCR后处理：补全截断的文字（如"等奖"→"一等奖"）
        from app.services.ocr_post_processor import process_ocr_text
        post_process_result = process_ocr_text(cert_text)
        processed_text = post_process_result['processed_text']

        if post_process_result.get('fixes'):
            logger.info(f"[学生证书上传] OCR后处理应用{len(post_process_result['fixes'])}个修复: "
                       f"{[f.get('type') for f in post_process_result['fixes']]}")
            for fix in post_process_result['fixes']:
                if fix.get('type') == 'award_level_completion':
                    logger.info(f"[学生证书上传]   奖项补全: '{fix.get('original')}' -> '{fix.get('replacement')}'")
            # 使用处理后的文本进行后续分析
            cert_text_for_analysis = processed_text
        else:
            cert_text_for_analysis = cert_text

        rag_rules = None
        if settings.RAG_ENABLED:
            try:
                rag_client = get_rag_client()
                rag_result = await rag_client.calculate_score(
                    certificate_text=cert_text_for_analysis,  # 使用后处理后的文本
                    student_info={
                        "student_id": current_user.user_id,
                        "username": current_user.username
                    }
                )
                rag_rules = rag_result.get("rag_rules", [])
            except Exception as e:
                logger.warning(f"获取RAG规则失败: {e}")
                rag_rules = None

        classification_result = await cert_service.classify_and_calculate_score(
            certificate_text=cert_text_for_analysis,  # 使用后处理后的文本
            certificate_info=certificate_info,
            student_info={
                "student_id": current_user.user_id,
                "username": current_user.username
            },
            rag_rules=rag_rules
        )
        
        certificate = await db_service.create_certificate(
            student_id=current_user.user_id,
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            title=certificate_info.get("title"),
            level=certificate_info.get("level"),
            issuer=certificate_info.get("issuer"),
            issue_date=certificate_info.get("issue_date"),
            raw_text=cert_text,
            category=classification_result["category"],
            score=classification_result["score"],
            classification_reason=classification_result.get("reason"),
            ocr_result=recognition_results,
            certificate_info=certificate_info,
            status="approved"
        )
        
        try:
            now = datetime.now()
            current_semester = "春季学期" if now.month >= 2 and now.month <= 7 else "秋季学期"
            current_academic_year = f"{now.year}-{now.year + 1}" if now.month >= 9 else f"{now.year - 1}-{now.year}"
            
            await db_service.update_comprehensive_score_with_certificates(
                student_id=current_user.user_id,
                semester=current_semester,
                academic_year=current_academic_year
            )
            logger.info(f"综测分数更新成功: student_id={current_user.user_id}")
        except Exception as e:
            logger.warning(f"更新综测分数失败（证书已保存）: {e}")
        
        logger.info(
            f"学生 {current_user.username} 上传证书成功: {file_id}, "
            f"类别={classification_result['category']}, 分数={classification_result['score']}"
        )
        
        certificate_info_with_score = {
            **certificate_info,
            "rag_score": {
                "score": classification_result["score"],
                "category": classification_result["category"],
                "rules": classification_result.get("reason", ""),
                "confidence": classification_result.get("confidence", 0.0),
                "rag_used": classification_result.get("rag_used", False),
                "rag_rules": classification_result.get("rag_rules", []),
                "scoring_rubric": classification_result.get("scoring_rubric", {}),
                "method": classification_result.get("method", "unknown")
            }
        }
        
        return {
            "success": True,
            "message": "证书上传成功",
            
            "file_id": file_id,
            "filename": file.filename,
            "file_size": file_size,
            "file_path": file_path,
            
            "recognition_results": recognition_results,
            
            "certificate_info": certificate_info_with_score,
            
            "raw_text": cert_text,
            
            "category": classification_result["category"],
            "score": classification_result["score"],
            "reason": classification_result.get("reason", ""),
            
            "rag_used": classification_result.get("rag_used", False),
            "rag_rules": classification_result.get("rag_rules", []),
            "rag_confidence": classification_result.get("confidence", 0.0),
            "rag_method": classification_result.get("method", "unknown"),
            "scoring_rubric": classification_result.get("scoring_rubric", {}),
            
            "certificate_id": certificate.get("id") if isinstance(certificate, dict) else certificate.id if certificate else None,
            "processed_at": datetime.now().isoformat(),
            
            "upload_result": {
                "file_id": file_id,
                "filename": file.filename,
                "file_size": file_size,
                "file_path": file_path
            },
            "ocr_result": {
                "recognition_results": recognition_results,
                "certificate_info": certificate_info,
                "raw_text": cert_text
            },
            "rag_result": {
                "used_rag": classification_result.get("rag_used", False),
                "retrieved_rules": classification_result.get("rag_rules", []),
                "confidence": classification_result.get("confidence", 0.0),
                "method": classification_result.get("method", "unknown")
            },
            "score_result": {
                "category": classification_result["category"],
                "score": classification_result["score"],
                "reason": classification_result.get("reason", ""),
                "scoring_rubric": classification_result.get("scoring_rubric", {})
            }
        }
    
    except Exception as e:
        logger.error(f"上传证书失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传证书失败: {str(e)}")


@router.post("/certificate/upload/batch")
async def upload_certificates_batch(
    files: List[UploadFile] = File(..., description="获奖证书图片列表"),
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service),
    upload_service: UploadService = Depends(get_upload_service)
) -> Dict[str, Any]:
    """批量上传获奖证书
    
    支持批量上传多张证书图片，自动识别、分类和算分
    """
    try:
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="单次最多上传20张证书")
        
        # 导入服务
        from app.services.certificate_service import get_certificate_service
        from app.services.ocr_service import get_ocr_service
        cert_service = get_certificate_service()
        ocr_service = get_ocr_service()
        executor = get_executor()
        
        results = []
        success_count = 0
        failed_count = 0
        
        for file in files:
            try:
                # 验证文件
                upload_service.validate_image_file(file)
                
                # 保存文件
                file_path, file_id = await upload_service.save_uploaded_file(file)
                
                # 读取文件内容
                file.file.seek(0)
                file_content = await file.read()
                file_size = len(file_content)
                
                # 创建文件记录
                await db_service.create_file(
                    id=file_id,
                    filename=file.filename,
                    file_type=file.content_type,
                    file_size=file_size,
                    file_path=file_path,
                    student_id=current_user.user_id
                )
                
                # OCR识别
                recognition_results = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    ocr_service.recognize_text,
                    file_path,
                    None
                )
                
                certificate_info = ocr_service.extract_certificate_info(
                    image_path=file_path,
                    ocr_results=recognition_results
                )
                
                # 获取证书文本
                cert_text = certificate_info.get("raw_text", "")
                if not cert_text:
                    cert_text = " ".join([item.get("text", "") for item in recognition_results])

                # OCR后处理：补全截断的文字（如"等奖"→"一等奖"）
                from app.services.ocr_post_processor import process_ocr_text
                post_process_result = process_ocr_text(cert_text)
                processed_text = post_process_result['processed_text']

                if post_process_result.get('fixes'):
                    logger.info(f"[批量上传] 文件{filename} OCR后处理应用{len(post_process_result['fixes'])}个修复")
                    cert_text_for_analysis = processed_text
                else:
                    cert_text_for_analysis = cert_text

                # 分类和算分
                classification_result = await cert_service.classify_and_calculate_score(
                    certificate_text=cert_text_for_analysis,  # 使用后处理后的文本
                    certificate_info=certificate_info,
                    student_info={
                        "student_id": current_user.user_id,
                        "username": current_user.username
                    }
                )
                
                # 保存证书记录
                certificate = await db_service.create_certificate(
                    student_id=current_user.user_id,
                    file_id=file_id,
                    filename=file.filename,
                    file_path=file_path,
                    title=certificate_info.get("title"),
                    level=certificate_info.get("level"),
                    issuer=certificate_info.get("issuer"),
                    issue_date=certificate_info.get("issue_date"),
                    raw_text=cert_text,
                    category=classification_result["category"],
                    score=classification_result["score"],
                    classification_reason=classification_result.get("reason"),
                    ocr_result=recognition_results,
                    certificate_info=certificate_info,
                    status="approved"
                )
                
                # 添加分类结果
                certificate_info["classification"] = classification_result
                
                results.append({
                    "file_id": file_id,
                    "filename": file.filename,
                    "success": True,
                    "category": classification_result["category"],
                    "score": classification_result["score"],
                    "certificate_info": certificate_info
                })
                success_count += 1
                
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}", exc_info=True)
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
                failed_count += 1
        
        # 获取证书汇总
        cert_summary = await db_service.get_student_certificates_summary(
            student_id=current_user.user_id,
            status="approved"
        )
        
        try:
            now = datetime.now()
            current_semester = "春季学期" if now.month >= 2 and now.month <= 7 else "秋季学期"
            current_academic_year = f"{now.year}-{now.year + 1}" if now.month >= 9 else f"{now.year - 1}-{now.year}"
            
            await db_service.update_comprehensive_score_with_certificates(
                student_id=current_user.user_id,
                semester=current_semester,
                academic_year=current_academic_year
            )
            logger.info(f"批量上传后综测分数更新成功: student_id={current_user.user_id}")
        except Exception as e:
            logger.warning(f"批量上传后更新综测分数失败: {e}")
        
        logger.info(
            f"学生 {current_user.username} 批量上传证书完成: "
            f"成功={success_count}, 失败={failed_count}"
        )
        
        return {
            "success": True,
            "message": f"批量上传完成: 成功{success_count}张, 失败{failed_count}张",
            "results": results,
            "summary": cert_summary
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量上传证书失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量上传证书失败: {str(e)}")


@router.get("/scores/summary")
async def get_score_summary(
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
) -> Dict[str, Any]:
    """获取学生综合成绩摘要
    
    返回学生的综测总分、各项得分等信息
    """
    try:
        # 从数据库查询实际成绩
        from app.utils.business_logic import get_student_scores_from_db
        score_data = await get_student_scores_from_db(current_user.user_id)
        
        # 获取证书汇总
        cert_summary = await db_service.get_student_certificates_summary(
            student_id=current_user.user_id,
            status="approved"
        )
        
        # 更新A类和C类分数
        if "a_score" not in score_data:
            score_data["a_score"] = cert_summary["a_total_score"]
        if "c_score" not in score_data:
            score_data["c_score"] = cert_summary["c_total_score"]
        
        # 获取证书列表
        certificates = await db_service.get_certificates(
            student_id=current_user.user_id,
            status="approved"
        )
        
        cert_list = []
        for cert in certificates:
            cert_list.append({
                "id": cert.id,
                "title": cert.title,
                "level": cert.level,
                "category": cert.category,
                "score": cert.score,
                "issue_date": cert.issue_date
            })
        
        score_data["certificates"] = cert_list
        score_data["certificate_summary"] = cert_summary
        
        return score_data
    
    except Exception as e:
        logger.error(f"获取成绩摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取成绩摘要失败: {str(e)}")


@router.get("/scores/detail")
async def get_score_detail(
    current_user: TokenData = Depends(get_student_user)
) -> Dict[str, Any]:
    """获取学生各项详细成绩"""
    return {
        "student_id": current_user.user_id,
        "username": current_user.username,
        "academic_scores": [
            {"course": "高等数学", "score": 92, "credit": 4},
            {"course": "大学英语", "score": 88, "credit": 3},
            {"course": "计算机基础", "score": 95, "credit": 3}
        ],
        "moral_activities": [
            {"activity": "志愿服务", "hours": 20, "score": 5.0},
            {"activity": "社团活动", "hours": 10, "score": 3.5}
        ],
        "certificates": []
    }


@router.get("/uploads")
async def get_upload_history(
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取学生上传历史记录"""
    try:
        # 从数据库查询该学生的所有上传文件
        files = await db_service.get_files(student_id=current_user.user_id)
        
        # 格式化返回数据
        upload_history = []
        for file in files:
            upload_history.append({
                "id": file.id,
                "filename": file.filename,
                "type": "certificate",  # 根据文件类型区分
                "status": "completed",  # 可以根据处理状态设置
                "score": None,  # 从RAG结果或数据库获取加分
                "upload_time": file.created_at.strftime("%Y-%m-%d %H:%M:%S") if file.created_at else None,
                "file_size": file.file_size,
                "remark": None
            })
        
        logger.info(f"学生 {current_user.username} 查询上传历史，共 {len(upload_history)} 条记录")
        return upload_history
    
    except Exception as e:
        logger.error(f"获取上传历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取上传历史失败: {str(e)}")


@router.get("/certificates")
async def list_my_certificates(
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """查看我的获奖证书列表"""
    try:
        # 从数据库查询学生的证书记录
        certificates = await db_service.get_certificates(
            student_id=current_user.user_id
        )
        
        # 格式化返回数据
        cert_list = []
        for cert in certificates:
            cert_list.append({
                "id": cert.id,
                "title": cert.title,
                "level": cert.level,
                "issuer": cert.issuer,
                "issue_date": cert.issue_date,
                "category": cert.category,
                "score": cert.score,
                "status": cert.status,
                "filename": cert.filename,
                "classification_reason": cert.classification_reason,
                "created_at": cert.created_at.isoformat() if cert.created_at else None
            })
        
        # 获取证书汇总
        summary = await db_service.get_student_certificates_summary(
            student_id=current_user.user_id,
            status="approved"
        )
        
        return {
            "total": len(cert_list),
            "certificates": cert_list,
            "summary": summary
        }
    
    except Exception as e:
        logger.error(f"获取证书列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取证书列表失败: {str(e)}")


@router.get("/comprehensive/analysis")
async def get_comprehensive_analysis(
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
) -> Dict[str, Any]:
    """获取学生综合分析
    
    返回学生的综合素质分析，包括学业成绩、证书加分、排名等信息
    """
    try:
        # 获取成绩摘要
        from app.utils.business_logic import get_student_scores_from_db
        score_data = await get_student_scores_from_db(current_user.user_id)
        
        # 获取证书汇总
        cert_summary = await db_service.get_student_certificates_summary(
            student_id=current_user.user_id,
            status="approved"
        )
        
        # 更新A类和C类分数
        if "a_score" not in score_data:
            score_data["a_score"] = cert_summary["a_total_score"]
        if "c_score" not in score_data:
            score_data["c_score"] = cert_summary["c_total_score"]
        
        # 计算综合分析数据
        comprehensive_analysis = {
            "student_id": current_user.user_id,
            "username": current_user.username,
            "academic_performance": {
                "b_score": score_data.get("b_score", 0),
                "rank": score_data.get("rank", 0),
                "class_rank": score_data.get("class_rank", 0),
                "major_rank": score_data.get("major_rank", 0)
            },
            "certificate_performance": {
                "a_score": score_data.get("a_score", 0),
                "c_score": score_data.get("c_score", 0),
                "total_certificates": cert_summary.get("total_count", 0),
                "categories": cert_summary.get("categories", {})
            },
            "comprehensive_score": {
                "total": score_data.get("total_score", 0),
                "a_percentage": round(score_data.get("a_score", 0) / max(score_data.get("total_score", 1), 1) * 100, 2),
                "b_percentage": round(score_data.get("b_score", 0) / max(score_data.get("total_score", 1), 1) * 100, 2),
                "c_percentage": round(score_data.get("c_score", 0) / max(score_data.get("total_score", 1), 1) * 100, 2)
            },
            "suggestions": [
                "继续加强专业课程学习，提高学业成绩",
                "积极参与各类竞赛和活动，增加证书加分",
                "注意平衡各项发展，提高综合素质"
            ]
        }
        
        return comprehensive_analysis
    
    except Exception as e:
        logger.error(f"获取综合分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取综合分析失败: {str(e)}")


@router.get("/scores/trend")
async def get_score_trend(
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
) -> Dict[str, Any]:
    """获取学生成绩趋势
    
    返回学生历次成绩变化趋势
    """
    try:
        # 获取学业成绩记录
        scores = await db_service.get_academic_scores(
            student_id=current_user.user_id
        )
        
        # 获取证书汇总（按时间排序）
        certificates = await db_service.get_certificates(
            student_id=current_user.user_id,
            status="approved"
        )
        
        # 按学期分组成绩数据
        semester_scores = {}
        for score in scores:
            semester_key = f"{score.academic_year}-{score.semester}"
            if semester_key not in semester_scores:
                semester_scores[semester_key] = {
                    "academic_year": score.academic_year,
                    "semester": score.semester,
                    "arithmetic_average": score.arithmetic_average,
                    "weighted_average": score.weighted_average,
                    "average_gpa": score.average_gpa,
                    "certificate_scores": 0
                }
        
        # 按时间分组证书数据
        cert_by_semester = {}
        for cert in certificates:
            # 根据证书颁发日期确定学期
            issue_date = cert.issue_date
            if issue_date:
                # 简单处理：根据月份判断学期
                month = int(issue_date.split('-')[1]) if '-' in issue_date else 1
                year = int(issue_date.split('-')[0]) if '-' in issue_date else 2024
                
                if month >= 2 and month <= 7:
                    semester = "1"
                    academic_year = f"{year}-{year+1}"
                else:
                    semester = "2"
                    if month >= 8:
                        academic_year = f"{year}-{year+1}"
                    else:
                        academic_year = f"{year-1}-{year}"
                
                semester_key = f"{academic_year}-{semester}"
                if semester_key not in cert_by_semester:
                    cert_by_semester[semester_key] = 0
                cert_by_semester[semester_key] += cert.score
        
        # 合并成绩和证书数据
        trend_data = []
        for semester_key in sorted(semester_scores.keys()):
            semester_data = semester_scores[semester_key]
            semester_data["certificate_scores"] = cert_by_semester.get(semester_key, 0)
            semester_data["total_score"] = (
                semester_data["arithmetic_average"] + 
                semester_data["certificate_scores"]
            )
            trend_data.append(semester_data)
        
        return {
            "student_id": current_user.user_id,
            "username": current_user.username,
            "trend_data": trend_data,
            "summary": {
                "total_semesters": len(trend_data),
                "average_score": sum(s["arithmetic_average"] for s in trend_data) / len(trend_data) if trend_data else 0,
                "highest_score": max(s["arithmetic_average"] for s in trend_data) if trend_data else 0,
                "lowest_score": min(s["arithmetic_average"] for s in trend_data) if trend_data else 0,
                "total_certificate_score": sum(s["certificate_scores"] for s in trend_data)
            }
        }
    
    except Exception as e:
        logger.error(f"获取成绩趋势失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取成绩趋势失败: {str(e)}")


@router.post("/material/upload")
async def upload_material(
    file: UploadFile = File(..., description="材料文件"),
    material_type: str = "other",
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service),
    upload_service: UploadService = Depends(get_upload_service)
):
    """学生上传材料
    
    上传各种材料文件（如申请材料、证明材料等）
    """
    try:
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file.content_type}，支持类型: {allowed_types}"
            )
        
        file_path, file_id = await upload_service.save_uploaded_file(file)
        
        file.file.seek(0)
        file_content = await file.read()
        file_size = len(file_content)
        
        file_record = await db_service.create_file(
            id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_type=material_type,
            file_size=file_size,
            student_id=current_user.user_id
        )
        
        logger.info(f"学生上传材料成功: {current_user.user_id} - {file.filename}")
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "file_size": file_size,
            "material_type": material_type,
            "message": "材料上传成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传材料失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传材料失败: {str(e)}")


@router.get("/materials")
async def get_materials(
    material_type: str = None,
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取学生上传的材料列表"""
    try:
        files = await db_service.get_files(
            student_id=current_user.user_id,
            file_type=material_type
        )
        
        materials = []
        for f in files:
            materials.append({
                "id": f.id,
                "filename": f.filename,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "file_path": f.file_path if hasattr(f, 'file_path') else None,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "status": f.status if hasattr(f, 'status') else "uploaded"
            })
        
        return {
            "student_id": current_user.user_id,
            "materials": materials,
            "total": len(materials)
        }
    
    except Exception as e:
        logger.error(f"获取材料列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取材料列表失败: {str(e)}")


@router.get("/materials/{material_id}")
async def get_material_detail(
    material_id: str,
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取单个材料的详细信息"""
    try:
        file_record = await db_service.get_file(file_id=material_id)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="材料不存在")
        
        if str(file_record.student_id) != str(current_user.user_id):
            raise HTTPException(status_code=403, detail="无权查看此材料")
        
        import os
        file_exists = file_record.file_path and os.path.exists(file_record.file_path)
        
        return {
            "success": True,
            "id": file_record.id,
            "filename": file_record.filename,
            "file_type": file_record.file_type,
            "file_size": file_record.file_size,
            "file_path": file_record.file_path,
            "file_exists": file_exists,
            "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
            "student_id": file_record.student_id,
            "preview_url": f"/v1/student/materials/{material_id}/preview" if file_exists else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取材料详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取材料详情失败: {str(e)}")


@router.get("/materials/{material_id}/preview")
async def preview_material(
    material_id: str,
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """预览/下载已上传的材料文件（图片/PDF）"""
    try:
        from fastapi.responses import FileResponse
        
        file_record = await db_service.get_file(file_id=material_id)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="材料不存在")
        
        if str(file_record.student_id) != str(current_user.user_id):
            raise HTTPException(status_code=403, detail="无权预览此材料")
        
        import os
        if not file_record.file_path or not os.path.exists(file_record.file_path):
            raise HTTPException(status_code=404, detail="文件不存在或已被删除")
        
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf'
        }
        
        _, ext = os.path.splitext(file_record.file_path)
        media_type = media_types.get(ext.lower(), 'application/octet-stream')
        
        logger.info(f"学生 {current_user.username} 预览材料: {material_id} - {file_record.filename}")
        
        return FileResponse(
            path=file_record.file_path,
            filename=file_record.filename,
            media_type=media_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览材料失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览材料失败: {str(e)}")


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: str,
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """删除学生上传的材料"""
    try:
        file_record = await db_service.get_file(file_id=material_id)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="材料不存在")
        
        if str(file_record.student_id) != str(current_user.user_id):
            raise HTTPException(status_code=403, detail="无权删除此材料")
        
        import os
        if file_record.file_path and os.path.exists(file_record.file_path):
            try:
                os.remove(file_record.file_path)
                logger.info(f"删除材料文件成功: {file_record.file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败(记录仍会删除): {e}")
        
        deleted = await db_service.delete_file(file_id=material_id)
        
        if not deleted:
            raise HTTPException(status_code=500, detail="删除材料失败")
        
        logger.info(f"学生 {current_user.username} 删除材料成功: material_id={material_id}")
        
        return {
            "success": True,
            "message": "材料删除成功",
            "material_id": material_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除材料失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除材料失败: {str(e)}")

