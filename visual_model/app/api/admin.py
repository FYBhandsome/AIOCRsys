#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员API路由
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Dict, Any, List

from app.models.auth import TokenData
from app.core.auth_middleware import get_admin_user
from app.services.rag_client import get_rag_client
from app.core.logger import logger


router = APIRouter(prefix="/admin", tags=["管理员"])


# ============================================================================
# 综测规则管理（对接RAG系统）
# ============================================================================

@router.post("/rules/upload")
async def upload_rule_document(
    file: UploadFile = File(..., description="规则文档（txt/pdf/docx）"),
    description: str = "",
    current_user: TokenData = Depends(get_admin_user)
):
    """管理员上传综测规则文档
    
    文档将被上传到RAG系统进行向量化处理
    """
    try:
        logger.info(f"管理员 {current_user.username} 上传规则文档: {file.filename}")
        
        # 保存临时文件
        import tempfile
        import os
        from pathlib import Path
        
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"rule_{file.filename}")
        
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 上传到RAG系统
        rag_client = get_rag_client()
        result = await rag_client.upload_document(
            file_path=temp_file_path,
            description=description
        )
        
        # 删除临时文件
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        logger.info(f"规则文档上传成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"上传规则文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传规则文档失败: {str(e)}")


@router.get("/rules/list")
async def list_rule_documents(
    enabled_only: bool = False,
    current_user: TokenData = Depends(get_admin_user)
):
    """获取规则文档列表"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.list_documents(enabled_only=enabled_only)
        return result
    except Exception as e:
        logger.error(f"获取规则文档列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取规则文档列表失败: {str(e)}")


@router.patch("/rules/{doc_id}/status")
async def update_rule_status(
    doc_id: str,
    enabled: bool,
    current_user: TokenData = Depends(get_admin_user)
):
    """启用/停用规则文档"""
    try:
        logger.info(f"管理员 {current_user.username} 更新规则文档 {doc_id} 状态: {enabled}")
        
        rag_client = get_rag_client()
        result = await rag_client.update_document_status(doc_id, enabled)
        return result
    except Exception as e:
        logger.error(f"更新规则文档状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新规则文档状态失败: {str(e)}")


@router.delete("/rules/{doc_id}")
async def delete_rule_document(
    doc_id: str,
    delete_file: bool = False,
    current_user: TokenData = Depends(get_admin_user)
):
    """删除规则文档"""
    try:
        logger.info(f"管理员 {current_user.username} 删除规则文档: {doc_id}")
        
        rag_client = get_rag_client()
        result = await rag_client.delete_document(doc_id, delete_file)
        return result
    except Exception as e:
        logger.error(f"删除规则文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除规则文档失败: {str(e)}")


# ============================================================================
# AI大模型配置管理（对接RAG系统）
# ============================================================================

@router.get("/ai/config")
async def get_ai_config(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取AI大模型配置"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.get_llm_config()
        return result
    except Exception as e:
        logger.error(f"获取AI配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取AI配置失败: {str(e)}")


@router.put("/ai/config")
async def update_ai_config(
    config: Dict[str, Any],
    current_user: TokenData = Depends(get_admin_user)
):
    """更新AI大模型配置
    
    请求体示例：
    {
        "enabled": true,
        "provider": "xunfei",
        "api_key": "your-api-key",
        "api_base_url": "http://maas-api.cn-huabei-1.xf-yun.com/v1",
        "model_id": "qwen3-1.7b",
        "temperature": 0.1,
        "max_tokens": 1024
    }
    """
    try:
        logger.info(f"管理员 {current_user.username} 更新AI配置")
        
        rag_client = get_rag_client()
        result = await rag_client.update_llm_config(config)
        return result
    except Exception as e:
        logger.error(f"更新AI配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新AI配置失败: {str(e)}")


@router.post("/ai/config/test")
async def test_ai_connection(
    current_user: TokenData = Depends(get_admin_user)
):
    """测试AI连接"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.test_llm_connection()
        return result
    except Exception as e:
        logger.error(f"测试AI连接失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试AI连接失败: {str(e)}")


@router.post("/ai/config/reset")
async def reset_ai_config(
    current_user: TokenData = Depends(get_admin_user)
):
    """重置AI配置为默认值"""
    try:
        logger.info(f"管理员 {current_user.username} 重置AI配置")
        
        rag_client = get_rag_client()
        result = await rag_client.reset_llm_config()
        return result
    except Exception as e:
        logger.error(f"重置AI配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重置AI配置失败: {str(e)}")


@router.get("/ai/config/validate")
async def validate_ai_config(
    current_user: TokenData = Depends(get_admin_user)
):
    """验证AI配置"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.validate_llm_config()
        return result
    except Exception as e:
        logger.error(f"验证AI配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证AI配置失败: {str(e)}")


# ============================================================================
# Prompt管理（对接RAG系统）
# ============================================================================

@router.get("/prompts")
async def get_prompts(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取Prompt配置"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.get_prompts()
        return result
    except Exception as e:
        logger.error(f"获取Prompt配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取Prompt配置失败: {str(e)}")


@router.put("/prompts")
async def update_prompts(
    prompts: Dict[str, Any],
    current_user: TokenData = Depends(get_admin_user)
):
    """更新Prompt配置
    
    请求体示例：
    {
        "system_prompt": "你是综测加分规则解析专家...",
        "user_prompt": "证书信息：{query}",
        "chat_system_prompt": "你是综测助手..."
    }
    """
    try:
        logger.info(f"管理员 {current_user.username} 更新Prompt配置")
        
        rag_client = get_rag_client()
        result = await rag_client.update_prompts(prompts)
        return result
    except Exception as e:
        logger.error(f"更新Prompt配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新Prompt配置失败: {str(e)}")


@router.post("/prompts/reset")
async def reset_prompts(
    current_user: TokenData = Depends(get_admin_user)
):
    """重置Prompt配置为默认值"""
    try:
        logger.info(f"管理员 {current_user.username} 重置Prompt配置")
        
        rag_client = get_rag_client()
        result = await rag_client.reset_prompts()
        return result
    except Exception as e:
        logger.error(f"重置Prompt配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重置Prompt配置失败: {str(e)}")


# ============================================================================
# 向量数据库管理（对接RAG系统）
# ============================================================================

@router.get("/vector-db/stats")
async def get_vector_db_stats(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取向量数据库统计信息"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.get_vector_db_stats()
        return result
    except Exception as e:
        logger.error(f"获取向量数据库统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取向量数据库统计失败: {str(e)}")


@router.post("/vector-db/reset")
async def reset_vector_db(
    confirm: bool = True,
    rebuild: bool = False,
    current_user: TokenData = Depends(get_admin_user)
):
    """重置向量数据库
    
    查询参数：
    - confirm: 确认重置（默认true）
    - rebuild: 是否立即重建（默认false）
    """
    try:
        logger.info(f"管理员 {current_user.username} 重置向量数据库")
        
        rag_client = get_rag_client()
        result = await rag_client.reset_vector_db(confirm=confirm, rebuild=rebuild)
        return result
    except Exception as e:
        logger.error(f"重置向量数据库失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重置向量数据库失败: {str(e)}")


@router.post("/vector-db/rebuild")
async def rebuild_vector_db(
    current_user: TokenData = Depends(get_admin_user)
):
    """重建向量数据库"""
    try:
        logger.info(f"管理员 {current_user.username} 重建向量数据库")
        
        rag_client = get_rag_client()
        result = await rag_client.rebuild_vector_db()
        return result
    except Exception as e:
        logger.error(f"重建向量数据库失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重建向量数据库失败: {str(e)}")


# ============================================================================
# RAG系统信息
# ============================================================================

@router.get("/rag/stats")
async def get_rag_stats(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取RAG系统统计信息"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.get_system_stats()
        return result
    except Exception as e:
        logger.error(f"获取RAG统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取RAG统计信息失败: {str(e)}")


@router.get("/rag/health")
async def rag_health_check(
    current_user: TokenData = Depends(get_admin_user)
):
    """RAG系统健康检查"""
    try:
        rag_client = get_rag_client()
        result = await rag_client.health_check()
        return result
    except Exception as e:
        logger.error(f"RAG健康检查失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG健康检查失败: {str(e)}")


# ============================================================================
# 系统设置
# ============================================================================

@router.get("/settings")
async def get_system_settings(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取系统设置"""
    from config import settings
    
    return {
        "ocr": {
            "threshold": settings.OCR_THRESHOLD,
            "use_gpu": settings.OCR_USE_GPU,
            "use_angle_cls": settings.OCR_USE_ANGLE_CLS,
            "max_image_size": settings.OCR_MAX_IMAGE_SIZE
        },
        "rag": {
            "base_url": settings.RAG_BASE_URL,
            "enabled": settings.RAG_ENABLED
        },
        "jwt": {
            "expiration_hours": settings.JWT_EXPIRATION_HOURS
        }
    }


@router.put("/settings")
async def update_system_settings(
    settings_data: Dict[str, Any],
    current_user: TokenData = Depends(get_admin_user)
):
    """更新系统设置
    
    注意：部分设置需要重启服务才能生效
    """
    logger.info(f"管理员 {current_user.username} 更新系统设置")
    
    # TODO: 实现设置持久化
    return {
        "message": "系统设置已更新（部分设置需重启服务）",
        "settings": settings_data
    }


# ============================================================================
# 用户管理
# ============================================================================

@router.get("/users")
async def list_users(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取用户列表"""
    # TODO: 从数据库查询用户
    return {
        "total": 0,
        "users": []
    }


@router.post("/users")
async def create_user(
    user_data: Dict[str, Any],
    current_user: TokenData = Depends(get_admin_user)
):
    """创建新用户"""
    logger.info(f"管理员 {current_user.username} 创建新用户")
    
    # TODO: 实现用户创建
    return {"message": "用户创建成功"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """删除用户"""
    logger.info(f"管理员 {current_user.username} 删除用户: {user_id}")
    
    # TODO: 实现用户删除
    return {"message": "用户删除成功"}

