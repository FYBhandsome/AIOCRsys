"""
工具模块
提供项目通用的业务逻辑和辅助功能
"""

from .business_logic import (
    # 用户管理
    get_users_from_db,
    create_user_in_db,
    delete_user_from_db,
    
    # 学生成绩管理
    get_student_scores_from_db,
)

__all__ = [
    'get_users_from_db',
    'create_user_in_db',
    'delete_user_from_db',
    'get_student_scores_from_db',
]

