#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库管理API路由
提供数据库清理、重置、统计等功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil
import sqlite3
import time
from datetime import datetime

from app.core.logger import get_logger
from app.core.config_manager import settings

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
        from app.rag.loaders.enhanced_loader import EnhancedRuleLoader
        
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
