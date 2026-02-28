#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理API路由
支持文件上传、下载、分片上传
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Header, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from typing import List, Optional
import json
from datetime import datetime

from app.services.file_upload_service import get_file_upload_service
from app.services.file_download_service import get_file_download_service
from app.models.tortoise_models import FileMetadata
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/file", tags=["文件管理"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="文件"),
    file_type: str = Form(..., description="文件类型: transcript, photo, certificate, template, result"),
    owner_id: str = Form(..., description="所有者ID(学号/工号)"),
    owner_type: str = Form("student", description="所有者类型: student, teacher, admin"),
    is_public: bool = Form(False, description="是否公开"),
    metadata: Optional[str] = Form(None, description="扩展元数据JSON")
):
    """
    上传单个文件
    
    Args:
        file: 上传的文件
        file_type: 文件类型
        owner_id: 所有者ID
        owner_type: 所有者类型
        is_public: 是否公开
        metadata: 扩展元数据
    
    Returns:
        上传结果
    """
    logger.info(f"上传文件: {file.filename}, type={file_type}, owner={owner_id}")
    
    try:
        content = await file.read()
        
        meta_dict = None
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except json.JSONDecodeError:
                meta_dict = {"raw": metadata}
        
        service = get_file_upload_service()
        result = await service.upload_file(
            file_content=content,
            original_filename=file.filename,
            file_type=file_type,
            owner_id=owner_id,
            owner_type=owner_type,
            is_public=is_public,
            metadata=meta_dict
        )
        
        if result["success"]:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "上传失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="文件列表"),
    file_type: str = Form(..., description="文件类型"),
    owner_id: str = Form(..., description="所有者ID"),
    owner_type: str = Form("student", description="所有者类型")
):
    """
    批量上传文件
    
    Args:
        files: 文件列表
        file_type: 文件类型
        owner_id: 所有者ID
        owner_type: 所有者类型
    
    Returns:
        批量上传结果
    """
    logger.info(f"批量上传: {len(files)}个文件, type={file_type}")
    
    try:
        file_list = []
        for file in files:
            content = await file.read()
            file_list.append((file.filename, content))
        
        service = get_file_upload_service()
        result = await service.upload_multiple_files(
            files=file_list,
            file_type=file_type,
            owner_id=owner_id,
            owner_type=owner_type
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"批量上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/chunk/init")
async def init_chunk_upload(
    filename: str = Form(..., description="文件名"),
    file_size: int = Form(..., description="文件总大小(字节)"),
    file_type: str = Form(..., description="文件类型"),
    owner_id: str = Form(..., description="所有者ID"),
    chunk_size: Optional[int] = Form(None, description="分片大小(字节)")
):
    """
    初始化分片上传
    
    Args:
        filename: 文件名
        file_size: 文件总大小
        file_type: 文件类型
        owner_id: 所有者ID
        chunk_size: 分片大小
    
    Returns:
        初始化结果，包含上传ID和分片信息
    """
    logger.info(f"初始化分片上传: {filename}, size={file_size}")
    
    service = get_file_upload_service()
    result = await service.init_chunk_upload(
        filename=filename,
        file_size=file_size,
        file_type=file_type,
        owner_id=owner_id,
        chunk_size=chunk_size
    )
    
    if result["success"]:
        return JSONResponse(content=result)
    else:
        raise HTTPException(status_code=400, detail=result.get("error"))


@router.post("/chunk/{file_id}/{chunk_index}")
async def upload_chunk(
    file_id: str,
    chunk_index: int,
    chunk: UploadFile = File(..., description="分片数据"),
    x_forwarded_for: Optional[str] = Header(None)
):
    """
    上传文件分片
    
    Args:
        file_id: 文件ID
        chunk_index: 分片序号
        chunk: 分片数据
        x_forwarded_for: 客户端IP
    
    Returns:
        上传结果
    """
    logger.info(f"上传分片: file={file_id}, chunk={chunk_index}")
    
    try:
        content = await chunk.read()
        upload_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else None
        
        service = get_file_upload_service()
        result = await service.upload_chunk(
            file_id=file_id,
            chunk_index=chunk_index,
            chunk_content=content,
            upload_ip=upload_ip
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"分片上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chunk/{file_id}/complete")
async def complete_chunk_upload(file_id: str):
    """
    完成分片上传，合并文件
    
    Args:
        file_id: 文件ID
    
    Returns:
        合并结果
    """
    logger.info(f"完成分片上传: {file_id}")
    
    service = get_file_upload_service()
    result = await service.complete_chunk_upload(file_id)
    
    if result["success"]:
        return JSONResponse(content=result)
    else:
        raise HTTPException(status_code=400, detail=result.get("error"))


@router.get("/chunk/{file_id}/progress")
async def get_upload_progress(file_id: str):
    """
    获取上传进度
    
    Args:
        file_id: 文件ID
    
    Returns:
        上传进度
    """
    service = get_file_upload_service()
    result = await service.get_upload_progress(file_id)
    
    return JSONResponse(content=result)


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    user_id: str = Query(..., description="用户ID"),
    user_type: str = Query("student", description="用户类型"),
    request: Request = None
):
    """
    下载文件
    
    Args:
        file_id: 文件ID
        user_id: 用户ID
        user_type: 用户类型
        request: 请求对象
    
    Returns:
        文件下载
    """
    logger.info(f"下载文件: {file_id}, user={user_id}")
    
    downloader_ip = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    service = get_file_download_service()
    result = await service.download_file(
        file_id=file_id,
        user_id=user_id,
        user_type=user_type,
        downloader_ip=downloader_ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        if result.get("code") == "PERMISSION_DENIED":
            raise HTTPException(status_code=403, detail=result.get("error"))
        raise HTTPException(status_code=404, detail=result.get("error"))
    
    return FileResponse(
        path=result["file_path"],
        filename=result["filename"],
        media_type=result.get("mime_type", "application/octet-stream")
    )


@router.get("/download/result/{file_id}")
async def download_result_file(
    file_id: str,
    user_id: str = Query(..., description="用户ID"),
    user_type: str = Query("student", description="用户类型"),
    request: Request = None
):
    """
    下载综测计算结果文件
    
    Args:
        file_id: 文件ID
        user_id: 用户ID
        user_type: 用户类型
    
    Returns:
        结果文件下载
    """
    logger.info(f"下载结果文件: {file_id}")
    
    downloader_ip = request.client.host if request else None
    
    service = get_file_download_service()
    result = await service.download_result_file(
        file_id=file_id,
        user_id=user_id,
        user_type=user_type,
        downloader_ip=downloader_ip
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    
    return FileResponse(
        path=result["file_path"],
        filename=result["filename"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/info/{file_id}")
async def get_file_info(file_id: str):
    """
    获取文件信息
    
    Args:
        file_id: 文件ID
    
    Returns:
        文件信息
    """
    service = get_file_download_service()
    result = await service.get_file_info(file_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error"))
    
    return JSONResponse(content=result)


@router.get("/list")
async def list_files(
    owner_id: Optional[str] = Query(None, description="所有者ID"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    status: Optional[str] = Query(None, description="状态"),
    limit: int = Query(20, description="返回数量"),
    offset: int = Query(0, description="偏移量")
):
    """
    列出文件
    
    Args:
        owner_id: 所有者ID
        file_type: 文件类型
        status: 状态
        limit: 返回数量
        offset: 偏移量
    
    Returns:
        文件列表
    """
    service = get_file_download_service()
    result = await service.list_files(
        owner_id=owner_id,
        file_type=file_type,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return JSONResponse(content=result)


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user_id: str = Query(..., description="用户ID"),
    user_type: str = Query("student", description="用户类型"),
    backup: bool = Query(True, description="是否创建备份")
):
    """
    删除文件
    
    Args:
        file_id: 文件ID
        user_id: 用户ID
        user_type: 用户类型
        backup: 是否创建备份
    
    Returns:
        删除结果
    """
    logger.info(f"删除文件: {file_id}, user={user_id}")
    
    service = get_file_download_service()
    result = await service.delete_file(
        file_id=file_id,
        user_id=user_id,
        user_type=user_type,
        create_backup=backup
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return JSONResponse(content=result)


@router.get("/download-history")
async def get_download_history(
    file_id: Optional[str] = Query(None, description="文件ID"),
    downloader_id: Optional[str] = Query(None, description="下载者ID"),
    limit: int = Query(50, description="返回数量")
):
    """
    获取下载历史
    
    Args:
        file_id: 文件ID
        downloader_id: 下载者ID
        limit: 返回数量
    
    Returns:
        下载历史
    """
    service = get_file_download_service()
    result = await service.get_download_history(
        file_id=file_id,
        downloader_id=downloader_id,
        limit=limit
    )
    
    return JSONResponse(content=result)


@router.get("/categories")
async def get_file_categories():
    """获取文件分类信息"""
    from app.services.file_upload_service import FileUploadService
    
    return JSONResponse(content={
        "categories": FileUploadService.FILE_CATEGORIES,
        "allowed_extensions": FileUploadService.ALLOWED_EXTENSIONS,
        "max_file_size": FileUploadService.MAX_FILE_SIZE,
        "chunk_size": FileUploadService.CHUNK_SIZE
    })
