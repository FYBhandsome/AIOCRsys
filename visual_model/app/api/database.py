#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理API - 仅限管理员
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.models.auth import TokenData
from app.core.auth_middleware import get_admin_user
from app.models.tortoise_models import (
    User, Student, Activity, ScoreRecord, 
    ComprehensiveScore, File
)
from app.core.logger import logger


router = APIRouter(
    prefix="/admin/database",
    tags=["数据库管理"],
    dependencies=[Depends(get_admin_user)]
)


class TableInfo(BaseModel):
    """数据表信息"""
    name: str
    description: str
    count: int


class DeleteRequest(BaseModel):
    """删除请求"""
    table: str
    ids: Optional[List[int]] = None  # 如果为None，则删除所有数据


# 数据表映射
TABLE_MODELS = {
    "users": User,
    "students": Student,
    "activities": Activity,
    "score_records": ScoreRecord,
    "comprehensive_scores": ComprehensiveScore,
    "files": File
}

TABLE_DESCRIPTIONS = {
    "users": "用户信息表",
    "students": "学生信息表",
    "activities": "学生活动表",
    "score_records": "分数记录表",
    "comprehensive_scores": "综测类别总成绩表",
    "files": "文件表"
}


@router.get("/tables", response_model=List[TableInfo])
async def list_tables(current_user: TokenData = Depends(get_admin_user)):
    """获取所有数据表信息
    
    返回数据库中所有表的名称、描述和记录数
    """
    try:
        tables_info = []
        
        for table_name, model in TABLE_MODELS.items():
            count = await model.all().count()
            tables_info.append(TableInfo(
                name=table_name,
                description=TABLE_DESCRIPTIONS.get(table_name, ""),
                count=count
            ))
        
        logger.info(f"管理员 {current_user.username} 查询数据表列表")
        return tables_info
        
    except Exception as e:
        logger.error(f"获取数据表信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据表信息失败: {str(e)}"
        )


@router.get("/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    current_user: TokenData = Depends(get_admin_user),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数")
):
    """获取指定表的数据
    
    Args:
        table_name: 表名
        skip: 跳过记录数（分页）
        limit: 返回记录数（分页）
    """
    try:
        if table_name not in TABLE_MODELS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据表不存在: {table_name}"
            )
        
        model = TABLE_MODELS[table_name]
        
        # 获取总数
        total = await model.all().count()
        
        # 获取数据
        records = await model.all().offset(skip).limit(limit)
        
        # 转换为字典列表
        data = []
        for record in records:
            record_dict = {}
            for field in record._meta.fields_map.keys():
                value = getattr(record, field, None)
                # 转换日期时间为字符串
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                record_dict[field] = value
            data.append(record_dict)
        
        logger.info(f"管理员 {current_user.username} 查询表 {table_name} 数据 (skip={skip}, limit={limit})")
        
        return {
            "table": table_name,
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取表数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取表数据失败: {str(e)}"
        )


@router.get("/tables/{table_name}/count")
async def get_table_count(
    table_name: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """获取指定表的记录数"""
    try:
        if table_name not in TABLE_MODELS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据表不存在: {table_name}"
            )
        
        model = TABLE_MODELS[table_name]
        count = await model.all().count()
        
        logger.info(f"管理员 {current_user.username} 查询表 {table_name} 记录数: {count}")
        
        return {
            "table": table_name,
            "count": count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取表记录数失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取表记录数失败: {str(e)}"
        )


@router.delete("/tables/{table_name}/records/{record_id}")
async def delete_single_record(
    table_name: str,
    record_id: int,
    current_user: TokenData = Depends(get_admin_user)
):
    """删除指定表中的单条记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
    """
    try:
        if table_name not in TABLE_MODELS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据表不存在: {table_name}"
            )
        
        model = TABLE_MODELS[table_name]
        
        # 查找记录
        record = await model.filter(id=record_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"记录不存在: ID={record_id}"
            )
        
        # 删除记录
        await record.delete()
        
        logger.warning(
            f"管理员 {current_user.username} 删除了表 {table_name} 中的记录: ID={record_id}"
        )
        
        return {
            "message": "记录删除成功",
            "table": table_name,
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除记录失败: {str(e)}"
        )


@router.delete("/tables/{table_name}/clear")
async def clear_table(
    table_name: str,
    current_user: TokenData = Depends(get_admin_user),
    confirm: str = Query(..., description="确认删除，请输入表名")
):
    """清空指定表的所有数据
    
    ⚠️ 危险操作！将删除表中的所有数据
    
    Args:
        table_name: 表名
        confirm: 确认字符串，必须与表名相同
    """
    try:
        # 确认检查
        if confirm != table_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="确认字符串不匹配，请输入正确的表名以确认删除"
            )
        
        if table_name not in TABLE_MODELS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据表不存在: {table_name}"
            )
        
        model = TABLE_MODELS[table_name]
        
        # 获取删除前的记录数
        count_before = await model.all().count()
        
        # 删除所有记录
        await model.all().delete()
        
        logger.warning(
            f"管理员 {current_user.username} 清空了表 {table_name}，删除了 {count_before} 条记录"
        )
        
        return {
            "message": f"表 {table_name} 已清空",
            "deleted_count": count_before
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空表失败: {str(e)}"
        )


@router.delete("/clear-all")
async def clear_all_tables(
    current_user: TokenData = Depends(get_admin_user),
    confirm: str = Query(..., description="确认删除，请输入: DELETE_ALL_DATA")
):
    """清空所有数据表
    
    ⚠️⚠️⚠️ 极度危险操作！将删除数据库中的所有数据
    
    Args:
        confirm: 确认字符串，必须是 "DELETE_ALL_DATA"
    """
    try:
        # 确认检查
        if confirm != "DELETE_ALL_DATA":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="确认字符串错误，请输入 'DELETE_ALL_DATA' 以确认删除所有数据"
            )
        
        deleted_counts = {}
        total_deleted = 0
        
        # 遍历所有表并清空
        for table_name, model in TABLE_MODELS.items():
            count = await model.all().count()
            if count > 0:
                await model.all().delete()
                deleted_counts[table_name] = count
                total_deleted += count
        
        logger.critical(
            f"管理员 {current_user.username} 清空了所有数据表，共删除 {total_deleted} 条记录"
        )
        
        return {
            "message": "所有数据表已清空",
            "deleted_counts": deleted_counts,
            "total_deleted": total_deleted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空所有表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空所有表失败: {str(e)}"
        )


@router.get("/stats")
async def get_database_stats(current_user: TokenData = Depends(get_admin_user)):
    """获取数据库统计信息
    
    返回所有表的记录数和总计
    """
    try:
        stats = {}
        total_records = 0
        
        for table_name, model in TABLE_MODELS.items():
            count = await model.all().count()
            stats[table_name] = {
                "description": TABLE_DESCRIPTIONS.get(table_name, ""),
                "count": count
            }
            total_records += count
        
        logger.info(f"管理员 {current_user.username} 查询数据库统计信息")
        
        return {
            "tables": stats,
            "total_records": total_records
        }
        
    except Exception as e:
        logger.error(f"获取数据库统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据库统计信息失败: {str(e)}"
        )

