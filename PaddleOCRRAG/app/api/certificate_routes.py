"""
证书相关API路由
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models import CertificateRequest, ApiResponse
from app.core.dependencies import DependencyContainer

# 创建依赖注入容器实例
container = DependencyContainer()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/certificate", tags=["证书管理"])


@router.post("/calculate")
async def calculate_certificate_points(request: CertificateRequest):
    """证书加分计算"""
    try:
        certificate_service = container.get_certificate_service()
        
        # 使用新的证书加分计算方法
        result = certificate_service.calculate_score(
            certificate_text=request.certificate_text,
            student_info=request.student_info
        )
        
        return ApiResponse(
            success=True,
            data=result,
            message="证书加分计算成功"
        )
    except Exception as e:
        logger.error(f"证书加分计算失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"证书加分计算失败: {str(e)}")


@router.post("/analyze")
async def analyze_certificate(request: CertificateRequest):
    """证书分析"""
    try:
        certificate_service = container.get_certificate_service()
        
        result = certificate_service.analyze_certificate(
            certificate_type="证书",
            certificate_level="",
            certificate_name=request.certificate_text,
            issue_date=""
        )
        
        return ApiResponse(
            success=True,
            data=result,
            message="证书分析成功"
        )
    except Exception as e:
        logger.error(f"证书分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"证书分析失败: {str(e)}")
