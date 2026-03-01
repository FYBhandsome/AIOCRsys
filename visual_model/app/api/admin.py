#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员API路由
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.models.auth import TokenData
from app.core.auth_middleware import get_admin_user
from app.services.rag_client import get_rag_client
from app.services.database_tortoise import DatabaseService
from app.services.dependencies import get_db_service
from app.services.comprehensive_score_service import get_comprehensive_score_calculation_service
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
        logger.info(f"管理员 {current_user.username} 获取规则文档列表, enabled_only={enabled_only}")
        
        rag_client = get_rag_client()
        result = await rag_client.list_documents(enabled_only=enabled_only)
        logger.info(f"获取规则文档列表成功: {result}")
        return result
    except Exception as e:
        logger.error(f"获取规则文档列表失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "documents": [],
            "message": f"RAG服务连接失败，请确保RAG服务正在运行。错误: {str(e)}"
        }


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
    
    from app.models.tortoise_models import SystemSetting
    import json
    
    updated_keys = []
    errors = []
    
    for key, value in settings_data.items():
        try:
            setting_type = "json"
            if isinstance(value, bool):
                setting_type = "boolean"
            elif isinstance(value, (int, float)):
                setting_type = "number"
            elif isinstance(value, str):
                setting_type = "string"
            
            setting_value = json.dumps(value) if not isinstance(value, str) else value
            
            await SystemSetting.update_or_create(
                setting_key=key,
                defaults={
                    "setting_value": setting_value,
                    "setting_type": setting_type,
                    "updated_by": current_user.username
                }
            )
            updated_keys.append(key)
        except Exception as e:
            errors.append({"key": key, "error": str(e)})
            logger.error(f"保存设置 {key} 失败: {e}")
    
    return {
        "message": f"系统设置已更新（{len(updated_keys)}项）",
        "updated_keys": updated_keys,
        "errors": errors if errors else None
    }


# ============================================================================
# 用户管理
# ============================================================================

@router.get("/users")
async def list_users(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取用户列表"""
    # 从数据库查询用户
    from app.utils.business_logic import get_users_from_db
    users = await get_users_from_db()
    
    return {
        "total": len(users),
        "users": users
    }


@router.post("/users")
async def create_user(
    user_data: Dict[str, Any],
    current_user: TokenData = Depends(get_admin_user)
):
    """创建新用户"""
    logger.info(f"管理员 {current_user.username} 创建新用户")
    
    # 实现用户创建
    from app.utils.business_logic import create_user_in_db
    try:
        result = await create_user_in_db(user_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """删除用户"""
    logger.info(f"管理员 {current_user.username} 删除用户: {user_id}")
    
    # 实现用户删除
    from app.utils.business_logic import delete_user_from_db
    try:
        result = await delete_user_from_db(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 综测配置管理
# ============================================================================

class ComprehensiveScoreConfigCreate(BaseModel):
    """创建综测配置请求模型"""
    name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    a_weight: float = Field(20.0, description="A类材料权重（%）", ge=0, le=100)
    b_weight: float = Field(70.0, description="B类材料（学习成绩）权重（%）", ge=0, le=100)
    c_weight: float = Field(10.0, description="C类材料权重（%）", ge=0, le=100)
    academic_score_field: str = Field(
        "weighted_average",
        description="学业成绩使用的字段",
        pattern="^(arithmetic_average|weighted_average|average_gpa|average_credit_gpa|credit_gpa_sum)$"
    )
    academic_score_scale: float = Field(1.0, description="学业成绩缩放系数", gt=0)
    is_active: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否为默认配置")
    applicable_grade: Optional[str] = Field(None, description="适用年级")
    applicable_semester: Optional[str] = Field(None, description="适用学期")


class ComprehensiveScoreConfigUpdate(BaseModel):
    """更新综测配置请求模型"""
    name: Optional[str] = Field(None, description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    a_weight: Optional[float] = Field(None, description="A类材料权重（%）", ge=0, le=100)
    b_weight: Optional[float] = Field(None, description="B类材料（学习成绩）权重（%）", ge=0, le=100)
    c_weight: Optional[float] = Field(None, description="C类材料权重（%）", ge=0, le=100)
    academic_score_field: Optional[str] = Field(
        None,
        description="学业成绩使用的字段",
        pattern="^(arithmetic_average|weighted_average|average_gpa|average_credit_gpa|credit_gpa_sum)$"
    )
    academic_score_scale: Optional[float] = Field(None, description="学业成绩缩放系数", gt=0)
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认配置")
    applicable_grade: Optional[str] = Field(None, description="适用年级")
    applicable_semester: Optional[str] = Field(None, description="适用学期")


@router.get("/comprehensive-score-config/fields")
async def get_available_academic_fields(
    current_user: TokenData = Depends(get_admin_user)
):
    """获取可选的学业成绩字段列表
    
    返回所有可用于计算综测成绩的学业成绩字段，包括中文标签、描述、推荐缩放系数等信息。
    """
    return {
        "fields": [
            {
                "value": "arithmetic_average",
                "label": "算术平均分",
                "english_name": "Arithmetic Average",
                "description": "所有课程成绩的算术平均值，不考虑学分权重",
                "scale": 1.0,
                "range": "0-100",
                "unit": "分"
            },
            {
                "value": "weighted_average",
                "label": "学分加权平均分",
                "english_name": "Weighted Average",
                "description": "按学分加权的平均分，反映课程学分对总成绩的影响",
                "scale": 1.0,
                "range": "0-100",
                "unit": "分",
                "recommended": True
            },
            {
                "value": "average_gpa",
                "label": "平均绩点",
                "english_name": "Average GPA",
                "description": "GPA平均值（4分制），需转换为百分制使用",
                "scale": 25.0,
                "range": "0-4",
                "unit": "GPA"
            },
            {
                "value": "average_credit_gpa",
                "label": "平均学分绩点",
                "english_name": "Average Credit GPA",
                "description": "按学分加权的GPA（4分制），需转换为百分制使用",
                "scale": 25.0,
                "range": "0-4",
                "unit": "GPA"
            },
            {
                "value": "credit_gpa_sum",
                "label": "学分绩点和",
                "english_name": "Credit GPA Sum",
                "description": "总学分绩点和，适用于特定计算场景",
                "scale": 1.0,
                "range": "varies",
                "unit": "点"
            }
        ]
    }


@router.post("/comprehensive-score-config", status_code=201)
async def create_comprehensive_score_config(
    config_data: ComprehensiveScoreConfigCreate,
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """创建综测配置
    
    配置包括：
    - A/B/C类材料权重比例
    - 学业成绩（B类）使用的字段
    - 学业成绩缩放系数（GPA转百分制等）
    """
    try:
        logger.info(f"管理员 {current_user.username} 创建综测配置: {config_data.name}")
        
        # 验证权重总和
        total_weight = config_data.a_weight + config_data.b_weight + config_data.c_weight
        if abs(total_weight - 100.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"权重总和必须为100%，当前为{total_weight}%"
            )
        
        # 创建配置
        config = await db_service.create_comprehensive_score_config(
            name=config_data.name,
            description=config_data.description,
            a_weight=config_data.a_weight,
            b_weight=config_data.b_weight,
            c_weight=config_data.c_weight,
            academic_score_field=config_data.academic_score_field,
            academic_score_scale=config_data.academic_score_scale,
            is_active=config_data.is_active,
            is_default=config_data.is_default,
            applicable_grade=config_data.applicable_grade,
            applicable_semester=config_data.applicable_semester
        )
        
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "a_weight": config.a_weight,
            "b_weight": config.b_weight,
            "c_weight": config.c_weight,
            "academic_score_field": config.academic_score_field,
            "academic_score_scale": config.academic_score_scale,
            "is_active": config.is_active,
            "is_default": config.is_default,
            "applicable_grade": config.applicable_grade,
            "applicable_semester": config.applicable_semester,
            "created_at": config.created_at.isoformat() if config.created_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建综测配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建综测配置失败: {str(e)}")


@router.get("/comprehensive-score-config")
async def list_comprehensive_score_configs(
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取综测配置列表"""
    try:
        configs = await db_service.get_comprehensive_score_configs(
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        config_list = []
        for config in configs:
            config_list.append({
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "a_weight": config.a_weight,
                "b_weight": config.b_weight,
                "c_weight": config.c_weight,
                "academic_score_field": config.academic_score_field,
                "academic_score_scale": config.academic_score_scale,
                "is_active": config.is_active,
                "is_default": config.is_default,
                "applicable_grade": config.applicable_grade,
                "applicable_semester": config.applicable_semester,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            })
        
        return {
            "total": len(config_list),
            "configs": config_list
        }
    
    except Exception as e:
        logger.error(f"获取综测配置列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取综测配置列表失败: {str(e)}")


@router.get("/comprehensive-score-config/{config_id}")
async def get_comprehensive_score_config(
    config_id: int,
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取单个综测配置"""
    try:
        config = await db_service.get_comprehensive_score_config(config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
        
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "a_weight": config.a_weight,
            "b_weight": config.b_weight,
            "c_weight": config.c_weight,
            "academic_score_field": config.academic_score_field,
            "academic_score_scale": config.academic_score_scale,
            "is_active": config.is_active,
            "is_default": config.is_default,
            "applicable_grade": config.applicable_grade,
            "applicable_semester": config.applicable_semester,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取综测配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取综测配置失败: {str(e)}")


@router.get("/comprehensive-score-config/default")
async def get_default_comprehensive_score_config(
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取默认综测配置"""
    try:
        config = await db_service.get_default_comprehensive_score_config()
        
        if not config:
            return {"message": "未设置默认配置"}
        
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "a_weight": config.a_weight,
            "b_weight": config.b_weight,
            "c_weight": config.c_weight,
            "academic_score_field": config.academic_score_field,
            "academic_score_scale": config.academic_score_scale,
            "applicable_grade": config.applicable_grade,
            "applicable_semester": config.applicable_semester
        }
    
    except Exception as e:
        logger.error(f"获取默认综测配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取默认综测配置失败: {str(e)}")


@router.put("/comprehensive-score-config/{config_id}")
async def update_comprehensive_score_config(
    config_id: int,
    config_data: ComprehensiveScoreConfigUpdate,
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """更新综测配置"""
    try:
        logger.info(f"管理员 {current_user.username} 更新综测配置: {config_id}")
        
        # 构建更新数据
        update_data = config_data.dict(exclude_unset=True)
        
        # 如果更新了权重，验证总和
        if any(k in update_data for k in ['a_weight', 'b_weight', 'c_weight']):
            # 获取当前配置
            config = await db_service.get_comprehensive_score_config(config_id)
            if not config:
                raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
            
            a_weight = update_data.get('a_weight', config.a_weight)
            b_weight = update_data.get('b_weight', config.b_weight)
            c_weight = update_data.get('c_weight', config.c_weight)
            
            total_weight = a_weight + b_weight + c_weight
            if abs(total_weight - 100.0) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"权重总和必须为100%，当前为{total_weight}%"
                )
        
        # 更新配置
        success = await db_service.update_comprehensive_score_config(config_id, **update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
        
        # 返回更新后的配置
        config = await db_service.get_comprehensive_score_config(config_id)
        
        return {
            "message": "配置更新成功",
            "config": {
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "a_weight": config.a_weight,
                "b_weight": config.b_weight,
                "c_weight": config.c_weight,
                "academic_score_field": config.academic_score_field,
                "academic_score_scale": config.academic_score_scale,
                "is_active": config.is_active,
                "is_default": config.is_default,
                "applicable_grade": config.applicable_grade,
                "applicable_semester": config.applicable_semester,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新综测配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新综测配置失败: {str(e)}")


@router.delete("/comprehensive-score-config/{config_id}")
async def delete_comprehensive_score_config(
    config_id: int,
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """删除综测配置"""
    try:
        logger.info(f"管理员 {current_user.username} 删除综测配置: {config_id}")
        
        success = await db_service.delete_comprehensive_score_config(config_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
        
        return {"message": "配置删除成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除综测配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除综测配置失败: {str(e)}")


@router.post("/comprehensive-score/calculate")
async def calculate_comprehensive_scores(
    config_id: int,
    semester: str,
    academic_year: str,
    class_name: Optional[str] = None,
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """批量计算并更新综测成绩
    
    根据指定的配置和学期，计算所有学生的综测成绩。
    
    请求参数：
    - config_id: 综测配置ID
    - semester: 学期
    - academic_year: 学年
    - class_name: 班级（可选，不指定则计算所有班级）
    """
    try:
        logger.info(
            f"管理员 {current_user.username} 批量计算综测成绩: "
            f"config_id={config_id}, semester={semester}, academic_year={academic_year}"
        )
        
        # 获取配置
        config = await db_service.get_comprehensive_score_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
        
        if not config.is_active:
            raise HTTPException(status_code=400, detail="配置未启用")
        
        # 获取学业成绩
        academic_scores = await db_service.get_academic_scores(
            semester=semester,
            academic_year=academic_year,
            class_name=class_name
        )
        
        if not academic_scores:
            return {
                "message": "没有找到符合条件的学业成绩",
                "processed": 0,
                "updated": 0,
                "failed": 0
            }
        
        # 计算综测成绩
        calc_service = get_comprehensive_score_calculation_service()
        
        processed = 0
        updated = 0
        failed = 0
        errors = []
        
        for academic_score in academic_scores:
            try:
                # 获取现有的综测成绩记录
                existing_comp_score = await db_service.get_comprehensive_scores(
                    student_id=academic_score.student_id,
                    semester=semester,
                    academic_year=academic_year
                )
                
                # 从证书汇总获取A类和C类成绩
                cert_summary = await db_service.get_student_certificates_summary(
                    student_id=academic_score.student_id,
                    status="approved"
                )
                
                a_score = cert_summary.get("a_total_score", 0.0)
                c_score = cert_summary.get("c_total_score", 0.0)
                
                # 如果已有记录，优先使用记录中的值（保留手动修改的分数）
                if existing_comp_score:
                    existing_a = existing_comp_score[0].a_total_score or 0.0
                    existing_c = existing_comp_score[0].c_total_score or 0.0
                    # 如果证书分数更高，则使用证书分数
                    if cert_summary.get("a_total_score", 0.0) > existing_a:
                        a_score = cert_summary.get("a_total_score", 0.0)
                    else:
                        a_score = existing_a
                    
                    if cert_summary.get("c_total_score", 0.0) > existing_c:
                        c_score = cert_summary.get("c_total_score", 0.0)
                    else:
                        c_score = existing_c
                
                # 计算综测成绩
                result = calc_service.calculate_comprehensive_score(
                    academic_score=academic_score,
                    config=config,
                    a_total_score=a_score,
                    c_total_score=c_score
                )
                
                # 更新或创建综测成绩记录
                await db_service.upsert_comprehensive_score(
                    student_id=academic_score.student_id,
                    semester=semester,
                    academic_year=academic_year,
                    a_total_score=result["a_total_score"],
                    b_total_score=result["b_total_score"],
                    c_total_score=result["c_total_score"],
                    total_score=result["total_score"],
                    remarks=f"使用配置: {config.name}"
                )
                
                processed += 1
                updated += 1
                
            except Exception as e:
                failed += 1
                logger.error(f"计算学生 {academic_score.student_id} 综测成绩失败: {e}")
                errors.append({
                    "student_id": academic_score.student_id,
                    "error": str(e)
                })
        
        return {
            "message": "综测成绩计算完成",
            "config": {
                "id": config.id,
                "name": config.name
            },
            "processed": processed,
            "updated": updated,
            "failed": failed,
            "errors": errors[:10] if errors else []  # 最多返回10个错误
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量计算综测成绩失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量计算综测成绩失败: {str(e)}")


@router.post("/comprehensive-score/preview")
async def preview_comprehensive_score_calculation(
    config_id: int,
    student_id: str,
    semester: str,
    academic_year: str,
    current_user: TokenData = Depends(get_admin_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """预览单个学生的综测成绩计算结果
    
    用于测试配置是否正确，不会保存到数据库。
    """
    try:
        # 获取配置
        config = await db_service.get_comprehensive_score_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
        
        # 获取学业成绩
        academic_scores = await db_service.get_academic_scores(
            student_id=student_id,
            semester=semester,
            academic_year=academic_year
        )
        
        if not academic_scores:
            raise HTTPException(
                status_code=404,
                detail=f"未找到学生 {student_id} 在 {semester}/{academic_year} 的学业成绩"
            )
        
        academic_score = academic_scores[0]
        
        # 获取现有的综测成绩记录
        existing_comp_score = await db_service.get_comprehensive_scores(
            student_id=student_id,
            semester=semester,
            academic_year=academic_year
        )
        
        a_score = 0.0
        c_score = 0.0
        if existing_comp_score:
            a_score = existing_comp_score[0].a_total_score or 0.0
            c_score = existing_comp_score[0].c_total_score or 0.0
        
        # 计算综测成绩
        calc_service = get_comprehensive_score_calculation_service()
        result = calc_service.calculate_comprehensive_score(
            academic_score=academic_score,
            config=config,
            a_total_score=a_score,
            c_total_score=c_score
        )
        
        # 返回详细信息
        return {
            "student_id": student_id,
            "student_name": academic_score.student_name,
            "semester": semester,
            "academic_year": academic_year,
            "config": {
                "id": config.id,
                "name": config.name,
                "a_weight": config.a_weight,
                "b_weight": config.b_weight,
                "c_weight": config.c_weight,
                "academic_score_field": config.academic_score_field,
                "academic_score_scale": config.academic_score_scale
            },
            "academic_score_raw": {
                "arithmetic_average": academic_score.arithmetic_average,
                "weighted_average": academic_score.weighted_average,
                "average_gpa": academic_score.average_gpa,
                "average_credit_gpa": academic_score.average_credit_gpa,
                "credit_gpa_sum": academic_score.credit_gpa_sum
            },
            "calculation": {
                "a_score": result["a_total_score"],
                "a_weighted": result["a_weighted_score"],
                "b_score": result["b_total_score"],
                "b_weighted": result["b_weighted_score"],
                "c_score": result["c_total_score"],
                "c_weighted": result["c_weighted_score"],
                "total_score": result["total_score"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览综测成绩计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览综测成绩计算失败: {str(e)}")

