"""
业务逻辑模块
包含各种业务逻辑处理函数
"""

import logging
from typing import Dict, Any, List, Optional
from app.services.database_tortoise import DatabaseService
from app.models.tortoise_models import AcademicScore, ComprehensiveScore
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)

async def get_student_scores_from_db(student_id: str, db_service: Optional[DatabaseService] = None) -> Dict[str, Any]:
    """从数据库获取学生成绩数据
    
    Args:
        student_id: 学生ID
        db_service: 数据库服务实例，如果为None则创建新实例
        
    Returns:
        包含学生成绩数据的字典，包括:
        - b_score: 学业成绩分数
        - a_score: 证书A类分数
        - c_score: 证书C类分数
        - total_score: 综测总分
        - rank: 总排名
        - class_rank: 班级排名
        - major_rank: 专业排名
    """
    try:
        # 如果没有提供数据库服务实例，则创建一个
        if db_service is None:
            from app.services.database_tortoise import get_db_service
            db_service = get_db_service()  # 不需要await，因为get_db_service不是协程
        
        # 获取最新的学业成绩记录
        academic_scores = await db_service.get_academic_scores(student_id=student_id)
        
        # 获取最新的综测成绩记录
        comprehensive_scores = await db_service.get_comprehensive_scores(student_id=student_id)
        
        # 默认返回值
        result = {
            "b_score": 0,  # 学业成绩分数
            "a_score": 0,  # 证书A类分数
            "c_score": 0,  # 证书C类分数
            "total_score": 0,  # 综测总分
            "rank": 0,  # 总排名
            "class_rank": 0,  # 班级排名
            "major_rank": 0  # 专业排名
        }
        
        # 处理学业成绩
        if academic_scores:
            # 取最新的学业成绩记录
            latest_academic_score = academic_scores[0]
            result["b_score"] = float(latest_academic_score.arithmetic_average or 0)
            
            # 如果有排名信息，也一并返回
            if latest_academic_score.arithmetic_average_rank:
                result["rank"] = latest_academic_score.arithmetic_average_rank
        
        # 处理综测成绩
        if comprehensive_scores:
            # 取最新的综测成绩记录
            latest_comprehensive_score = comprehensive_scores[0]
            result["total_score"] = float(latest_comprehensive_score.total_score or 0)
            result["a_score"] = float(latest_comprehensive_score.a_score or 0)
            result["c_score"] = float(latest_comprehensive_score.c_score or 0)
            
            # 如果有排名信息，也一并返回
            if latest_comprehensive_score.total_rank:
                result["rank"] = latest_comprehensive_score.total_rank
            if latest_comprehensive_score.class_rank:
                result["class_rank"] = latest_comprehensive_score.class_rank
            if latest_comprehensive_score.major_rank:
                result["major_rank"] = latest_comprehensive_score.major_rank
        
        logger.info(f"获取学生成绩数据成功: {student_id}")
        return result
        
    except Exception as e:
        logger.error(f"获取学生成绩数据失败: {e}", exc_info=True)
        # 返回默认值，避免前端出错
        return {
            "b_score": 0,
            "a_score": 0,
            "c_score": 0,
            "total_score": 0,
            "rank": 0,
            "class_rank": 0,
            "major_rank": 0,
            "error": str(e)
        }


async def get_users_from_db() -> List[Dict[str, Any]]:
    """从数据库获取用户列表
    
    Returns:
        用户列表，每个用户包含基本信息
    """
    try:
        from app.models.tortoise_models import User
        
        # 查询所有用户
        users = await User.all()
        
        # 转换为字典列表
        result = []
        for user in users:
            result.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "real_name": user.real_name,
                "student_id": user.student_id,
                "class_id": user.class_id,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })
        
        logger.info(f"获取用户列表成功，共 {len(result)} 个用户")
        return result
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}", exc_info=True)
        # 返回空列表，避免前端出错
        return []


async def create_user_in_db(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """在数据库中创建新用户
    
    Args:
        user_data: 用户数据字典
        
    Returns:
        创建的用户信息
    """
    try:
        from app.models.tortoise_models import User
        from app.core.auth import get_password_hash
        
        # 检查必填字段
        if not user_data.get("username") or not user_data.get("password"):
            raise ValueError("用户名和密码不能为空")
        
        # 检查用户名是否已存在
        existing_user = await User.filter(username=user_data["username"]).first()
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 创建新用户
        password_hash = get_password_hash(user_data["password"])
        user = await User.create(
            username=user_data["username"],
            email=user_data.get("email"),
            password=password_hash,
            role=user_data.get("role", "student"),
            real_name=user_data.get("real_name"),
            student_id=user_data.get("student_id"),
            class_id=user_data.get("class_id"),
            is_active=user_data.get("is_active", True)
        )
        
        result = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "real_name": user.real_name,
            "student_id": user.student_id,
            "class_id": user.class_id,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        
        logger.info(f"创建用户成功: {user.username}")
        return result
        
    except ValueError:
        raise  # 重新抛出验证错误
    except Exception as e:
        logger.error(f"创建用户失败: {e}", exc_info=True)
        raise ValueError(f"创建用户失败: {str(e)}")


async def delete_user_from_db(user_id: str) -> Dict[str, Any]:
    """从数据库中删除用户
    
    Args:
        user_id: 用户ID
        
    Returns:
        删除结果
    """
    try:
        from app.models.tortoise_models import User
        
        # 查找用户
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 删除用户
        username = user.username
        await user.delete()
        
        logger.info(f"删除用户成功: {username}")
        return {"success": True, "message": f"用户 {username} 已删除"}
        
    except ValueError:
        raise  # 重新抛出验证错误
    except Exception as e:
        logger.error(f"删除用户失败: {e}", exc_info=True)
        raise ValueError(f"删除用户失败: {str(e)}")