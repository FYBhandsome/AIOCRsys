"""
文档管理相关API路由
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from app.models import ApiResponse, DocumentStatusUpdate
from app.core.dependencies import DependencyContainer
from app.services.document_analyzer_service import get_document_analyzer_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["文档管理"])
document_analyzer_router = APIRouter(prefix="/document", tags=["文档分析"])

# 创建依赖注入容器实例
container = DependencyContainer()


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form(...),
    tags: str = Form(default="[]"),
    description: str = Form(default="")
):
    """上传文档"""
    try:
        document_service = container.get_document_service()
        
        result = document_service.upload_document(
            file=file,
            category=category,
            tags=tags,
            description=description
        )
        
        return ApiResponse(
            success=True,
            data=result,
            message="文档上传成功"
        )
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("")
async def list_documents(category: Optional[str] = None, tags: Optional[str] = None):
    """获取文档列表"""
    try:
        document_service = container.get_document_service()
        result = document_service.list_documents(category=category, tags=tags)
        
        return ApiResponse(
            success=True,
            data=result,
            message="获取文档列表成功"
        )
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.get("/{document_id}")
async def get_document(document_id: str):
    """获取文档详情"""
    try:
        document_service = container.get_document_service()
        document = document_service.get_document(document_id)
        
        if document is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return ApiResponse(
            success=True,
            data=document,
            message="获取文档详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    try:
        document_service = container.get_document_service()
        success = document_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return ApiResponse(
            success=True,
            data={
                "document_id": document_id,
                "deleted_at": datetime.now().isoformat()
            },
            message="文档删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档删除失败: {str(e)}")


@router.post("/{document_id}/enable")
async def enable_document(document_id: str):
    """启用文档"""
    try:
        document_service = container.get_document_service()
        success = document_service.update_document_status(document_id, enabled=True)
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return ApiResponse(
            success=True,
            data={
                "document_id": document_id,
                "enabled": True,
                "updated_at": datetime.now().isoformat()
            },
            message="文档启用成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档启用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档启用失败: {str(e)}")


@router.post("/{document_id}/disable")
async def disable_document(document_id: str):
    """停用文档"""
    try:
        document_service = container.get_document_service()
        success = document_service.update_document_status(document_id, enabled=False)
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return ApiResponse(
            success=True,
            data={
                "document_id": document_id,
                "enabled": False,
                "updated_at": datetime.now().isoformat()
            },
            message="文档停用成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档停用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档停用失败: {str(e)}")


@router.get("/{document_id}/status")
async def get_document_processing_status(document_id: str):
    """获取文档处理状态"""
    try:
        document_service = container.get_document_service()
        result = document_service.get_document_processing_status(document_id)
        
        return ApiResponse(
            success=True,
            data=result,
            message="获取文档处理状态成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取文档处理状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档处理状态失败: {str(e)}")


@document_analyzer_router.post("/analyze")
async def analyze_document(file_path: Optional[str] = None):
    """
    文档分析接口
    
    分析指定文档，返回结构化数据：
    - rules: 检索到的规则列表
    - ratios: 综测计算比例数据
    - analysis: 文档分析说明
    
    Args:
        file_path: 可选的文档路径，默认使用综测规则文档
    """
    logger.info(f"[analyze_document] 接收文档分析请求: file_path={file_path}")
    
    try:
        document_analyzer_service = get_document_analyzer_service()
        
        logger.debug(f"[analyze_document] 调用文档分析服务, file_path={file_path}")
        result = document_analyzer_service.analyze_document(file_path)
        
        if not result.get("success"):
            error_msg = result.get("error", "文档分析失败")
            logger.error(f"[analyze_document] 文档分析失败: {error_msg}")
            return ApiResponse(
                success=False,
                data={
                    "rules": [],
                    "ratios": {},
                    "analysis": "",
                    "error": error_msg
                },
                message=f"文档分析失败: {error_msg}"
            )
        
        logger.info(
            f"[analyze_document] 文档分析成功: rules_count={len(result.get('rules', []))}, "
            f"has_formula={result.get('ratios', {}).get('formula') is not None}"
        )
        
        return ApiResponse(
            success=True,
            data={
                "rules": result.get("rules", []),
                "ratios": result.get("ratios", {}),
                "analysis": result.get("analysis", ""),
                "metadata": result.get("metadata", {})
            },
            message="文档分析成功"
        )
        
    except Exception as e:
        error_msg = f"文档分析异常: {str(e)}"
        logger.error(f"[analyze_document] {error_msg}", exc_info=True)
        return ApiResponse(
            success=False,
            data={
                "rules": [],
                "ratios": {},
                "analysis": "",
                "error": error_msg
            },
            message=error_msg
        )


@router.get("/analyze/overview")
async def analyze_document_overview(file_path: Optional[str] = None):
    """
    文档分析概览接口
    
    返回文档的综测计算规则、比例数据和分析说明
    """
    try:
        analyzer_service = get_document_analyzer_service()
        result = analyzer_service.analyze_document(file_path)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "文档分析失败"))
        
        return ApiResponse(
            success=True,
            data={
                "rules": result.get("rules", []),
                "ratios": result.get("ratios", {}),
                "analysis": result.get("analysis", ""),
                "metadata": result.get("metadata", {})
            },
            message="文档分析成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档分析失败: {str(e)}")


@router.get("/analyze/rules")
async def get_document_rules(query: Optional[str] = None, top_k: int = 10):
    """
    获取文档计算规则
    
    通过RAG检索综测计算规则
    """
    try:
        analyzer_service = get_document_analyzer_service()
        result = analyzer_service.retrieve_rules_by_rag(query=query, top_k=top_k)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "规则检索失败"))
        
        return ApiResponse(
            success=True,
            data={
                "rules": result.get("rules", []),
                "total": result.get("total", 0),
                "query": result.get("query", "")
            },
            message="规则检索成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"规则检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"规则检索失败: {str(e)}")


@router.get("/analyze/ratios")
async def get_document_ratios():
    """
    获取综测计算比例数据
    
    返回公式：M=20%*A+70%*B+10%*C
    A—品德行为分，B—学习成绩分，C—素质拓展分
    """
    try:
        analyzer_service = get_document_analyzer_service()
        result = analyzer_service.extract_ratio_data()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "比例数据提取失败"))
        
        return ApiResponse(
            success=True,
            data={
                "formula": result.get("formula"),
                "ratios": result.get("ratios", {}),
                "components": result.get("components", {})
            },
            message="比例数据获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"比例数据获取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"比例数据获取失败: {str(e)}")


@router.get("/analyze/description")
async def get_document_analysis_description(max_length: int = 100):
    """
    获取文档分析说明
    
    返回100字以内的文档分析说明
    """
    try:
        analyzer_service = get_document_analyzer_service()
        analysis = analyzer_service.generate_analysis_description(max_length=max_length)
        
        return ApiResponse(
            success=True,
            data={
                "analysis": analysis,
                "length": len(analysis)
            },
            message="分析说明获取成功"
        )
    except Exception as e:
        logger.error(f"分析说明获取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析说明获取失败: {str(e)}")
