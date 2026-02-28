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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["文档管理"])

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
