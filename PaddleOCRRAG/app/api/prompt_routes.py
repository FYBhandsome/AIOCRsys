"""
Prompt管理相关API路由
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models import ApiResponse, PromptUpdateRequest
from app.core.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prompts", tags=["Prompt管理"])


@router.get("")
async def list_prompts():
    """获取Prompt列表"""
    try:
        # 获取所有自定义Prompt
        custom_prompts = prompt_manager.list_custom_prompts()
        
        # 添加系统内置Prompt
        system_prompts = [
            {
                "prompt_type": "system",
                "content": prompt_manager.system_prompt,
                "description": "系统默认Prompt",
                "updated_at": datetime.now().isoformat()
            },
            {
                "prompt_type": "user",
                "content": prompt_manager.user_prompt,
                "description": "用户Prompt",
                "updated_at": datetime.now().isoformat()
            },
            {
                "prompt_type": "chat_system",
                "content": prompt_manager.chat_system_prompt,
                "description": "聊天系统Prompt",
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        # 添加自定义Prompt
        for name, content in custom_prompts.items():
            system_prompts.append({
                "prompt_type": name,
                "content": content,
                "description": f"自定义Prompt: {name}",
                "updated_at": datetime.now().isoformat()
            })
        
        return ApiResponse(
            success=True,
            data={
                "prompts": system_prompts,
                "total": len(system_prompts)
            },
            message="获取Prompt列表成功"
        )
    except Exception as e:
        logger.error(f"获取Prompt列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取Prompt列表失败: {str(e)}")


@router.get("/{prompt_type}")
async def get_prompt(prompt_type: str):
    """获取特定类型的Prompt"""
    try:
        # 获取系统内置Prompt
        if prompt_type == "system":
            prompt_content = prompt_manager.system_prompt
            description = "系统默认Prompt"
        elif prompt_type == "user":
            prompt_content = prompt_manager.user_prompt
            description = "用户Prompt"
        elif prompt_type == "chat_system":
            prompt_content = prompt_manager.chat_system_prompt
            description = "聊天系统Prompt"
        else:
            # 获取自定义Prompt
            prompt_content = prompt_manager.get_custom_prompt(prompt_type)
            if prompt_content is None:
                raise HTTPException(status_code=404, detail="Prompt不存在")
            description = f"自定义Prompt: {prompt_type}"
        
        return ApiResponse(
            success=True,
            data={
                "prompt_type": prompt_type,
                "content": prompt_content,
                "description": description,
                "updated_at": datetime.now().isoformat()
            },
            message="获取Prompt成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Prompt失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取Prompt失败: {str(e)}")


@router.post("/{prompt_type}")
async def update_prompt(prompt_type: str, request: PromptUpdateRequest):
    """更新Prompt"""
    try:
        # 更新系统内置Prompt
        if prompt_type == "system":
            success = prompt_manager.update_prompt(system_prompt=request.content)
        elif prompt_type == "user":
            success = prompt_manager.update_prompt(user_prompt=request.content)
        elif prompt_type == "chat_system":
            success = prompt_manager.update_prompt(chat_system_prompt=request.content)
        else:
            # 更新或添加自定义Prompt
            success = prompt_manager.add_custom_prompt(prompt_type, request.content)
        
        if not success:
            raise HTTPException(status_code=500, detail="Prompt更新失败")
        
        return ApiResponse(
            success=True,
            data={
                "prompt_type": prompt_type,
                "content": request.content,
                "description": request.description,
                "updated_at": datetime.now().isoformat()
            },
            message="Prompt更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prompt更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prompt更新失败: {str(e)}")
