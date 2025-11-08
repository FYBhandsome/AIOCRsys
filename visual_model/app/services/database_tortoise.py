#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务 - 使用Tortoise ORM重构版本
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError

from app.core.logger import logger
from app.core.exceptions import DatabaseException
from app.core.db_connection import get_db_connection_manager
from app.models.tortoise_models import (
    User, Student, Activity, ScoreRecord, 
    ComprehensiveScore, File
)
from config import settings


class DatabaseService:
    """数据库服务 - 使用Tortoise ORM"""
    
    def __init__(self):
        """初始化数据库服务"""
        self.db_url = settings.DATABASE_URL
        self.tortoise_config = settings.TORTOISE_ORM
        self.db_manager = get_db_connection_manager()
        logger.info("数据库服务初始化完成")
    
    async def init_connection(self):
        """初始化数据库连接"""
        return await self.db_manager.init_connection()
    
    async def close_connection(self):
        """关闭数据库连接"""
        await self.db_manager.close_connection()
    
    # 用户相关操作
    async def create_user(self, student_id: str, password: str, role: str = "student", 
                         is_active: bool = True, extra_info: Dict[str, Any] = None) -> User:
        """创建用户"""
        try:
            user = await User.create(
                student_id=student_id,
                password=password,
                role=role,
                is_active=is_active,
                extra_info=extra_info
            )
            logger.info(f"创建用户成功: {student_id}")
            return user
        except IntegrityError as e:
            logger.error(f"创建用户失败，学号已存在: {student_id}")
            raise DatabaseException(f"创建用户失败，学号已存在: {student_id}")
        except Exception as e:
            logger.error(f"创建用户失败: {e}", exc_info=True)
            raise DatabaseException(f"创建用户失败: {str(e)}")
    
    async def get_user(self, user_id: int = None, student_id: str = None) -> Optional[User]:
        """获取用户"""
        try:
            if user_id:
                return await User.get_or_none(id=user_id)
            elif student_id:
                return await User.get_or_none(student_id=student_id)
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {e}", exc_info=True)
            raise DatabaseException(f"获取用户失败: {str(e)}")
    
    async def update_user(self, user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return False
            
            await user.update_from_dict(kwargs)
            await user.save()
            logger.info(f"更新用户信息成功: {user_id}")
            return True
        except DoesNotExist:
            logger.error(f"更新用户失败，用户不存在: {user_id}")
            return False
        except Exception as e:
            logger.error(f"更新用户失败: {e}", exc_info=True)
            raise DatabaseException(f"更新用户失败: {str(e)}")
    
    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return False
            
            await user.delete()
            logger.info(f"删除用户成功: {user_id}")
            return True
        except DoesNotExist:
            logger.error(f"删除用户失败，用户不存在: {user_id}")
            return False
        except Exception as e:
            logger.error(f"删除用户失败: {e}", exc_info=True)
            raise DatabaseException(f"删除用户失败: {str(e)}")
    
    # 学生相关操作
    async def create_student(self, id: str, name: str, college: str, major: str, 
                            class_name: str, grade: str, total_score: float = 0.0,
                            dormitory_number: str = None, dormitory_score: float = None,
                            physical_test_score: float = None) -> Student:
        """创建学生"""
        try:
            student = await Student.create(
                id=id,
                name=name,
                college=college,
                major=major,
                class_name=class_name,
                grade=grade,
                total_score=total_score,
                dormitory_number=dormitory_number,
                dormitory_score=dormitory_score,
                physical_test_score=physical_test_score
            )
            logger.info(f"创建学生成功: {id}")
            return student
        except IntegrityError as e:
            logger.error(f"创建学生失败，学号已存在: {id}")
            raise DatabaseException(f"创建学生失败，学号已存在: {id}")
        except Exception as e:
            logger.error(f"创建学生失败: {e}", exc_info=True)
            raise DatabaseException(f"创建学生失败: {str(e)}")
    
    async def get_student(self, student_id: str) -> Optional[Student]:
        """获取学生"""
        try:
            return await Student.get_or_none(id=student_id).prefetch_related(
                'activities', 'score_records', 'comprehensive_scores'
            )
        except Exception as e:
            logger.error(f"获取学生失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学生失败: {str(e)}")
    
    async def get_students(self, class_name: str = None, grade: str = None, 
                          college: str = None, major: str = None, 
                          limit: int = None, offset: int = None) -> List[Student]:
        """获取学生列表"""
        try:
            query = Student.all()
            
            if class_name:
                query = query.filter(class_name=class_name)
            if grade:
                query = query.filter(grade=grade)
            if college:
                query = query.filter(college=college)
            if major:
                query = query.filter(major=major)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return await query
        except Exception as e:
            logger.error(f"获取学生列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学生列表失败: {str(e)}")
    
    async def update_student(self, student_id: str, **kwargs) -> bool:
        """更新学生信息"""
        try:
            student = await Student.get_or_none(id=student_id)
            if not student:
                return False
            
            await student.update_from_dict(kwargs)
            await student.save()
            logger.info(f"更新学生信息成功: {student_id}")
            return True
        except DoesNotExist:
            logger.error(f"更新学生失败，学生不存在: {student_id}")
            return False
        except Exception as e:
            logger.error(f"更新学生失败: {e}", exc_info=True)
            raise DatabaseException(f"更新学生失败: {str(e)}")
    
    async def delete_student(self, student_id: str) -> bool:
        """删除学生"""
        try:
            student = await Student.get_or_none(id=student_id)
            if not student:
                return False
            
            await student.delete()
            logger.info(f"删除学生成功: {student_id}")
            return True
        except DoesNotExist:
            logger.error(f"删除学生失败，学生不存在: {student_id}")
            return False
        except Exception as e:
            logger.error(f"删除学生失败: {e}", exc_info=True)
            raise DatabaseException(f"删除学生失败: {str(e)}")
    
    # 活动相关操作
    async def create_activity(self, name: str, type: str, details: Dict[str, Any], 
                            score: float, student_id: str, 
                            status: str = "pending") -> Activity:
        """创建活动"""
        try:
            activity = await Activity.create(
                name=name,
                type=type,
                details=details,
                score=score,
                student_id=student_id,
                status=status
            )
            logger.info(f"创建活动成功: {name}")
            return activity
        except Exception as e:
            logger.error(f"创建活动失败: {e}", exc_info=True)
            raise DatabaseException(f"创建活动失败: {str(e)}")
    
    async def save_activity(self, activity) -> Activity:
        """保存活动"""
        try:
            await activity.save()
            logger.info(f"保存活动成功: {activity.id}")
            return activity
        except Exception as e:
            logger.error(f"保存活动失败: {e}", exc_info=True)
            raise DatabaseException(f"保存活动失败: {str(e)}")
    
    async def get_activity(self, activity_id: int) -> Optional[Activity]:
        """获取活动"""
        try:
            return await Activity.get_or_none(id=activity_id).prefetch_related('student')
        except Exception as e:
            logger.error(f"获取活动失败: {e}", exc_info=True)
            raise DatabaseException(f"获取活动失败: {str(e)}")
    
    async def get_activities(self, student_id: str = None, status: str = None, 
                           type: str = None, limit: int = None, 
                           offset: int = None) -> List[Activity]:
        """获取活动列表"""
        try:
            query = Activity.all()
            
            if student_id:
                query = query.filter(student_id=student_id)
            if status:
                query = query.filter(status=status)
            if type:
                query = query.filter(type=type)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return await query.prefetch_related('student')
        except Exception as e:
            logger.error(f"获取活动列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取活动列表失败: {str(e)}")
    
    async def update_activity(self, activity_id: int, **kwargs) -> bool:
        """更新活动信息"""
        try:
            activity = await Activity.get_or_none(id=activity_id)
            if not activity:
                return False
            
            await activity.update_from_dict(kwargs)
            await activity.save()
            logger.info(f"更新活动信息成功: {activity_id}")
            return True
        except DoesNotExist:
            logger.error(f"更新活动失败，活动不存在: {activity_id}")
            return False
        except Exception as e:
            logger.error(f"更新活动失败: {e}", exc_info=True)
            raise DatabaseException(f"更新活动失败: {str(e)}")
    
    async def delete_activity(self, activity_id: int) -> bool:
        """删除活动"""
        try:
            activity = await Activity.get_or_none(id=activity_id)
            if not activity:
                return False
            
            await activity.delete()
            logger.info(f"删除活动成功: {activity_id}")
            return True
        except DoesNotExist:
            logger.error(f"删除活动失败，活动不存在: {activity_id}")
            return False
        except Exception as e:
            logger.error(f"删除活动失败: {e}", exc_info=True)
            raise DatabaseException(f"删除活动失败: {str(e)}")
    
    # 分数记录相关操作
    async def create_score_record(self, total_score: float, details: Dict[str, Any], 
                                student_id: str) -> ScoreRecord:
        """创建分数记录"""
        try:
            score_record = await ScoreRecord.create(
                total_score=total_score,
                details=details,
                student_id=student_id
            )
            logger.info(f"创建分数记录成功: {total_score}")
            return score_record
        except Exception as e:
            logger.error(f"创建分数记录失败: {e}", exc_info=True)
            raise DatabaseException(f"创建分数记录失败: {str(e)}")
    
    async def save_score_record(self, score_record) -> ScoreRecord:
        """保存分数记录"""
        try:
            await score_record.save()
            logger.info(f"保存分数记录成功: {score_record.id}")
            return score_record
        except Exception as e:
            logger.error(f"保存分数记录失败: {e}", exc_info=True)
            raise DatabaseException(f"保存分数记录失败: {str(e)}")
    
    async def update_score_record(self, score_record) -> bool:
        """更新分数记录"""
        try:
            await score_record.save()
            logger.info(f"更新分数记录成功: {score_record.id}")
            return True
        except Exception as e:
            logger.error(f"更新分数记录失败: {e}", exc_info=True)
            raise DatabaseException(f"更新分数记录失败: {str(e)}")
    
    async def delete_score_record(self, score_id: str) -> bool:
        """删除分数记录"""
        try:
            score_record = await ScoreRecord.get_or_none(id=score_id)
            if not score_record:
                return False
            
            await score_record.delete()
            logger.info(f"删除分数记录成功: {score_id}")
            return True
        except DoesNotExist:
            logger.error(f"删除分数记录失败，记录不存在: {score_id}")
            return False
        except Exception as e:
            logger.error(f"删除分数记录失败: {e}", exc_info=True)
            raise DatabaseException(f"删除分数记录失败: {str(e)}")
    
    async def get_score_record(self, record_id: int) -> Optional[ScoreRecord]:
        """获取分数记录"""
        try:
            return await ScoreRecord.get_or_none(id=record_id).prefetch_related('student')
        except Exception as e:
            logger.error(f"获取分数记录失败: {e}", exc_info=True)
            raise DatabaseException(f"获取分数记录失败: {str(e)}")
    
    async def get_score_records(self, student_id: str = None, limit: int = None, 
                              offset: int = None) -> List[ScoreRecord]:
        """获取分数记录列表"""
        try:
            query = ScoreRecord.all()
            
            if student_id:
                query = query.filter(student_id=student_id)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return await query.prefetch_related('student')
        except Exception as e:
            logger.error(f"获取分数记录列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取分数记录列表失败: {str(e)}")
    
    # 综测成绩相关操作
    async def create_comprehensive_score(self, student_id: str, semester: str, 
                                       academic_year: str, **kwargs) -> ComprehensiveScore:
        """创建综测成绩"""
        try:
            comprehensive_score = await ComprehensiveScore.create(
                student_id=student_id,
                semester=semester,
                academic_year=academic_year,
                **kwargs
            )
            logger.info(f"创建综测成绩成功: {student_id}, {semester}")
            return comprehensive_score
        except Exception as e:
            logger.error(f"创建综测成绩失败: {e}", exc_info=True)
            raise DatabaseException(f"创建综测成绩失败: {str(e)}")
    
    async def get_comprehensive_score(self, score_id: int) -> Optional[ComprehensiveScore]:
        """获取综测成绩"""
        try:
            return await ComprehensiveScore.get_or_none(id=score_id).prefetch_related('student')
        except Exception as e:
            logger.error(f"获取综测成绩失败: {e}", exc_info=True)
            raise DatabaseException(f"获取综测成绩失败: {str(e)}")
    
    async def get_comprehensive_scores(self, student_id: str = None, semester: str = None, 
                                     academic_year: str = None, limit: int = None, 
                                     offset: int = None) -> List[ComprehensiveScore]:
        """获取综测成绩列表"""
        try:
            query = ComprehensiveScore.all()
            
            if student_id:
                query = query.filter(student_id=student_id)
            if semester:
                query = query.filter(semester=semester)
            if academic_year:
                query = query.filter(academic_year=academic_year)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return await query.prefetch_related('student')
        except Exception as e:
            logger.error(f"获取综测成绩列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取综测成绩列表失败: {str(e)}")
    
    # 文件相关操作
    async def create_file(self, id: str, filename: str, 
                         file_path: str, file_size: int, file_type: str, 
                         student_id: str = None) -> File:
        """创建文件记录"""
        try:
            file = await File.create(
                id=id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                student_id=student_id
            )
            logger.info(f"创建文件记录成功: {filename}")
            return file
        except Exception as e:
            logger.error(f"创建文件记录失败: {e}", exc_info=True)
            raise DatabaseException(f"创建文件记录失败: {str(e)}")
    
    async def get_file(self, file_id: str) -> Optional[File]:
        """获取文件记录"""
        try:
            return await File.get_or_none(id=file_id)
        except Exception as e:
            logger.error(f"获取文件记录失败: {e}", exc_info=True)
            raise DatabaseException(f"获取文件记录失败: {str(e)}")
    
    async def get_files(self, student_id: str = None, file_type: str = None, 
                        limit: int = None, offset: int = None) -> List[File]:
        """获取文件记录列表"""
        try:
            query = File.all()
            
            if student_id:
                query = query.filter(student_id=student_id)
            if file_type:
                query = query.filter(file_type=file_type)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return await query
        except Exception as e:
            logger.error(f"获取文件记录列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取文件记录列表失败: {str(e)}")
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件记录"""
        try:
            file = await File.get_or_none(id=file_id)
            if not file:
                return False
            
            await file.delete()
            logger.info(f"删除文件记录成功: {file_id}")
            return True
        except DoesNotExist:
            logger.error(f"删除文件记录失败，文件不存在: {file_id}")
            return False
        except Exception as e:
            logger.error(f"删除文件记录失败: {e}", exc_info=True)
            raise DatabaseException(f"删除文件记录失败: {str(e)}")


# 创建全局数据库服务实例
db_service = DatabaseService()


def get_db_service() -> DatabaseService:
    """获取数据库服务实例"""
    return db_service