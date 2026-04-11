#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库管理API路由
提供数据库清理、重置、统计等功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil
import sqlite3
import time
from datetime import datetime

from app.core.logger import get_logger
from app.core.config_manager import settings
from app.core.api_response import ResponseBuilder, ResponseCode

logger = get_logger(__name__)
router = APIRouter(prefix="/vector-db", tags=["向量数据库管理"])


class VectorDBStats(BaseModel):
    """向量数据库统计信息"""
    db_path: str
    exists: bool
    total_documents: int = 0
    collections: List[Dict[str, str]] = []
    db_size_bytes: int = 0
    db_size_formatted: str = "0 B"
    last_modified: Optional[str] = None


class ClearResult(BaseModel):
    """清理结果"""
    success: bool
    message: str
    cleared_documents: int = 0
    cleared_size_bytes: int = 0


class ResetResult(BaseModel):
    """重置结果"""
    success: bool
    message: str
    backup_path: Optional[str] = None


class RAGDocumentUploadResult(BaseModel):
    document_id: str
    filename: str
    chunk_count: int = 0
    status: str = "processed"
    message: str = ""


class RAGDocumentListItem(BaseModel):
    source_file: str
    chunk_count: int = 0
    category: Optional[str] = None


class RAGDocumentListResponse(BaseModel):
    documents: list = []
    total_documents: int = 0
    total_chunks: int = 0


class RAGDocumentDeleteResult(BaseModel):
    success: bool
    message: str
    deleted_count: int = 0


ALLOWED_RAG_FILE_TYPES = {".docx", ".txt", ".pdf", ".xlsx"}
MAX_RAG_FILE_SIZE = 50 * 1024 * 1024


def get_db_path() -> Path:
    """获取向量数据库路径"""
    return Path(settings.CHROMA_DB_PATH)


def get_sqlite_path() -> Path:
    """获取SQLite数据库文件路径"""
    return get_db_path() / "chroma.sqlite3"


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


@router.get("/stats", response_model=VectorDBStats, summary="获取向量数据库统计信息")
async def get_vector_db_stats():
    """
    获取向量数据库的详细统计信息
    
    包括：
    - 数据库路径和存在状态
    - 文档总数
    - 集合列表
    - 数据库大小
    - 最后修改时间
    """
    logger.info("[get_vector_db_stats] 获取向量数据库统计信息")
    
    db_path = get_db_path()
    sqlite_path = get_sqlite_path()
    
    stats = VectorDBStats(
        db_path=str(db_path),
        exists=db_path.exists()
    )
    
    if not db_path.exists():
        logger.warning(f"[get_vector_db_stats] 数据库目录不存在: {db_path}")
        return stats
    
    try:
        if sqlite_path.exists():
            stats.db_size_bytes = sqlite_path.stat().st_size
            stats.db_size_formatted = format_size(stats.db_size_bytes)
            stats.last_modified = datetime.fromtimestamp(
                sqlite_path.stat().st_mtime
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(str(sqlite_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name FROM collections;")
            collections = cursor.fetchall()
            stats.collections = [
                {"id": coll_id, "name": coll_name}
                for coll_id, coll_name in collections
            ]
            
            try:
                cursor.execute("SELECT COUNT(*) FROM embedding_fulltext_search;")
                stats.total_documents = cursor.fetchone()[0]
            except Exception:
                stats.total_documents = 0
            
            conn.close()
            
        logger.info(
            f"[get_vector_db_stats] 统计完成: 文档数={stats.total_documents}, "
            f"大小={stats.db_size_formatted}"
        )
        
    except Exception as e:
        logger.error(f"[get_vector_db_stats] 获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
    
    return stats


@router.post("/clear", response_model=ClearResult, summary="清空向量数据库")
async def clear_vector_db(background_tasks: BackgroundTasks):
    """
    清空向量数据库中的所有数据
    
    - 删除所有向量数据
    - 保留数据库结构
    - 返回清理的文档数和释放的空间
    """
    logger.info("[clear_vector_db] 开始清空向量数据库")
    
    db_path = get_db_path()
    
    if not db_path.exists():
        logger.warning("[clear_vector_db] 数据库目录不存在，无需清理")
        return ClearResult(
            success=True,
            message="数据库目录不存在，无需清理"
        )
    
    try:
        cleared_docs = 0
        cleared_size = 0
        
        sqlite_path = get_sqlite_path()
        if sqlite_path.exists():
            try:
                conn = sqlite3.connect(str(sqlite_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM embedding_fulltext_search;")
                cleared_docs = cursor.fetchone()[0]
                conn.close()
            except Exception:
                pass
            
            cleared_size = sqlite_path.stat().st_size
        
        for item in db_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        
        logger.info(
            f"[clear_vector_db] 清理完成: 清除{cleared_docs}个文档, "
            f"释放{format_size(cleared_size)}空间"
        )
        
        return ClearResult(
            success=True,
            message=f"成功清空向量数据库，清除{cleared_docs}个文档，释放{format_size(cleared_size)}空间",
            cleared_documents=cleared_docs,
            cleared_size_bytes=cleared_size
        )
        
    except Exception as e:
        logger.error(f"[clear_vector_db] 清空失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@router.post("/reset", response_model=ResetResult, summary="重置向量数据库")
async def reset_vector_db(background_tasks: BackgroundTasks, backup: bool = True):
    """
    重置向量数据库到初始状态
    
    - 可选择是否备份现有数据
    - 完全删除并重建数据库目录
    - 返回备份路径（如果创建了备份）
    """
    logger.info(f"[reset_vector_db] 开始重置向量数据库, backup={backup}")
    
    db_path = get_db_path()
    backup_path = None
    
    if not db_path.exists():
        logger.info("[reset_vector_db] 数据库目录不存在，创建新目录")
        db_path.mkdir(parents=True, exist_ok=True)
        return ResetResult(
            success=True,
            message="数据库目录不存在，已创建新目录"
        )
    
    try:
        if backup:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = db_path.parent / f"chroma_db_backup_{timestamp}"
            shutil.copytree(db_path, backup_path)
            logger.info(f"[reset_vector_db] 已创建备份: {backup_path}")
        
        shutil.rmtree(db_path)
        db_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("[reset_vector_db] 重置完成")
        
        return ResetResult(
            success=True,
            message="向量数据库已重置到初始状态",
            backup_path=str(backup_path) if backup_path else None
        )
        
    except Exception as e:
        logger.error(f"[reset_vector_db] 重置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")

# TODO: 增加或者完善上传RAG文档的功能

import uuid


@router.post("/documents/upload", summary="上传RAG文档")
async def upload_rag_document(
    file: UploadFile = File(...),
    category: str = Form(default="default"),
    description: str = Form(default="")
):
    logger.info(f"[upload_rag_document] 开始上传文档: {file.filename}, category={category}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_RAG_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}，允许的类型: {ALLOWED_RAG_FILE_TYPES}"
        )

    content = await file.read()
    if len(content) > MAX_RAG_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {format_size(len(content))}，最大允许: {format_size(MAX_RAG_FILE_SIZE)}"
        )

    document_id = str(uuid.uuid4())[:8]
    save_path = Path(settings.RULES_DOCS_PATH) / file.filename
    Path(settings.RULES_DOCS_PATH).mkdir(parents=True, exist_ok=True)

    try:
        with open(save_path, "wb") as f:
            f.write(content)

        from app.rag.vector_db import get_vector_db
        from app.rag import get_enhanced_rule_loader

        EnhancedRuleLoader, _ = get_enhanced_rule_loader()
        loader = EnhancedRuleLoader()
        file_path_str = str(save_path)

        if file_ext == ".docx":
            loader._load_docx(file_path_str, file.filename)
        elif file_ext == ".txt":
            loader._load_txt(file_path_str, file.filename)
        elif file_ext == ".pdf":
            loader._load_pdf(file_path_str, file.filename)
        elif file_ext == ".xlsx":
            loader._load_excel(file_path_str, file.filename)

        chunks = loader.get_chunks_as_dicts()
        chunk_count = len(chunks)

        if chunks:
            vector_db = get_vector_db()
            vector_db.add_documents(chunks)

        logger.info(
            f"[upload_rag_document] 上传完成: {file.filename}, chunks={chunk_count}"
        )

        return ResponseBuilder.success(
            data={
                "document_id": document_id,
                "filename": file.filename,
                "chunk_count": chunk_count,
                "status": "processed",
                "message": f"文档处理完成，生成{chunk_count}个文档块"
            },
            message="RAG文档上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[upload_rag_document] 上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文档上传处理失败: {str(e)}")


@router.get("/documents", summary="获取RAG文档列表")
async def list_rag_documents():
    logger.info("[list_rag_documents] 获取RAG文档列表")

    try:
        from app.rag.vector_db import get_vector_db

        vector_db = get_vector_db()
        result = vector_db.collection.get(include=["metadatas"])

        documents_map = {}
        total_chunks = 0

        if result and result.get("metadatas"):
            for meta in result["metadatas"]:
                source_file = meta.get("source_file", "unknown")
                cat = meta.get("category", None)

                if source_file not in documents_map:
                    documents_map[source_file] = {
                        "source_file": source_file,
                        "chunk_count": 0,
                        "category": cat
                    }

                documents_map[source_file]["chunk_count"] += 1
                total_chunks += 1

        documents_list = list(documents_map.values())

        logger.info(
            f"[list_rag_documents] 查询完成: 文档数={len(documents_list)}, 总chunks={total_chunks}"
        )

        return ResponseBuilder.success(
            data={
                "documents": documents_list,
                "total_documents": len(documents_list),
                "total_chunks": total_chunks
            },
            message="查询成功"
        )

    except Exception as e:
        logger.error(f"[list_rag_documents] 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.delete("/documents/{source_file}", summary="删除RAG文档")
async def delete_rag_document(source_file: str):
    logger.info(f"[delete_rag_document] 删除文档: {source_file}")

    try:
        from app.rag.vector_db import get_vector_db

        vector_db = get_vector_db()
        filtered_docs = vector_db.collection.get(
            where={"source_file": source_file},
            include=["metadatas"]
        )

        deleted_count = 0
        if filtered_docs and filtered_docs.get("ids"):
            deleted_count = len(filtered_docs["ids"])
            vector_db.delete_documents_by_filter({"source_file": source_file})

        logger.info(f"[delete_rag_document] 删除完成: {source_file}, 删除{deleted_count}个chunks")

        return ResponseBuilder.success(
            data={
                "success": True,
                "message": f"文档 {source_file} 已删除，共删除 {deleted_count} 个文档块",
                "deleted_count": deleted_count
            },
            message=f"成功删除文档，共删除{deleted_count}个文档块"
        )

    except Exception as e:
        logger.error(f"[delete_rag_document] 删除失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.post("/documents/process", summary="处理已有文件到向量库")
async def process_existing_file(file_path: str = Form(...)):
    logger.info(f"[process_existing_file] 处理文件: {file_path}")

    path_obj = Path(file_path)
    if not path_obj.exists():
        raise HTTPException(status_code=400, detail=f"文件不存在: {file_path}")

    file_ext = path_obj.suffix.lower()
    if file_ext not in ALLOWED_RAG_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}，允许的类型: {ALLOWED_RAG_FILE_TYPES}"
        )

    try:
        from app.rag.vector_db import get_vector_db
        from app.rag import get_enhanced_rule_loader

        EnhancedRuleLoader, _ = get_enhanced_rule_loader()
        loader = EnhancedRuleLoader()

        if file_ext == ".docx":
            loader._load_docx(str(path_obj), path_obj.name)
        elif file_ext == ".txt":
            loader._load_txt(str(path_obj), path_obj.name)
        elif file_ext == ".pdf":
            loader._load_pdf(str(path_obj), path_obj.name)
        elif file_ext == ".xlsx":
            loader._load_excel(str(path_obj), path_obj.name)

        chunks = loader.get_chunks_as_dicts()
        chunk_count = len(chunks)

        if chunks:
            vector_db = get_vector_db()
            vector_db.add_documents(chunks)

        logger.info(f"[process_existing_file] 处理完成: {path_obj.name}, chunks={chunk_count}")

        return ResponseBuilder.success(
            data={
                "filename": path_obj.name,
                "file_path": file_path,
                "chunk_count": chunk_count,
                "status": "processed",
                "message": f"文件处理完成，生成{chunk_count}个文档块"
            },
            message="文件处理成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[process_existing_file] 处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.post("/reindex", summary="重新索引文档")
async def reindex_documents(background_tasks: BackgroundTasks):
    """
    重新索引所有规则文档
    
    - 清空现有向量数据
    - 重新加载规则文档
    - 重新生成向量索引
    """
    logger.info("[reindex_documents] 开始重新索引文档")
    
    try:
        from app.rag.vector_db import get_vector_db
        from app.rag import get_enhanced_rule_loader

        EnhancedRuleLoader, _ = get_enhanced_rule_loader()
        vector_db = get_vector_db()
        loader = EnhancedRuleLoader()
        
        logger.info("[reindex_documents] 清空现有数据...")
        vector_db.clear_all_documents()
        
        logger.info("[reindex_documents] 加载文档...")
        loader.load_all_documents()
        
        chunks = loader.get_chunks_as_dicts()
        if chunks:
            logger.info(f"[reindex_documents] 添加{len(chunks)}个文档块...")
            vector_db.add_documents(chunks)
        
        stats = vector_db.get_category_stats()
        
        logger.info(
            f"[reindex_documents] 索引完成: 总文档数={stats.get('total', 0)}"
        )
        
        return {
            "success": True,
            "message": f"重新索引完成，共{stats.get('total', 0)}个文档",
            "total_documents": stats.get('total', 0),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"[reindex_documents] 重新索引失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重新索引失败: {str(e)}")


@router.get("/collections", summary="获取所有集合")
async def get_collections():
    """获取向量数据库中的所有集合"""
    logger.info("[get_collections] 获取集合列表")
    
    sqlite_path = get_sqlite_path()
    
    if not sqlite_path.exists():
        return {"collections": []}
    
    try:
        conn = sqlite3.connect(str(sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM collections;")
        collections = cursor.fetchall()
        
        result = [
            {"id": coll_id, "name": coll_name}
            for coll_id, coll_name in collections
        ]
        
        conn.close()
        
        return {"collections": result}
        
    except Exception as e:
        logger.error(f"[get_collections] 获取集合失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取集合失败: {str(e)}")


@router.get("/health", summary="数据库健康检查")
async def health_check():
    """检查向量数据库健康状态"""
    db_path = get_db_path()
    sqlite_path = get_sqlite_path()
    
    status = {
        "healthy": True,
        "db_exists": db_path.exists(),
        "sqlite_exists": sqlite_path.exists(),
        "writable": False,
        "document_count": 0
    }
    
    if db_path.exists():
        try:
            test_file = db_path / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
            status["writable"] = True
        except Exception:
            status["writable"] = False
            status["healthy"] = False
    
    if sqlite_path.exists():
        try:
            conn = sqlite3.connect(str(sqlite_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM embedding_fulltext_search;")
            status["document_count"] = cursor.fetchone()[0]
            conn.close()
        except Exception:
            status["healthy"] = False
    
    return status
