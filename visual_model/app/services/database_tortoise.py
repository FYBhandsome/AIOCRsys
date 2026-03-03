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
    User, Student, AcademicScore, 
    ComprehensiveScoreConfig, ComprehensiveScore, File, Certificate,
    Class, ClassStudent
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
                'academic_scores'
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
    
    # 班级相关操作
    async def save_class(self, class_obj) -> Class:
        """保存班级"""
        try:
            await class_obj.save()
            logger.info(f"保存班级成功: {class_obj.id}")
            return class_obj
        except Exception as e:
            logger.error(f"保存班级失败: {e}", exc_info=True)
            raise DatabaseException(f"保存班级失败: {str(e)}")
    
    async def get_class(self, class_id: str) -> Optional[Class]:
        """获取班级"""
        try:
            return await Class.get_or_none(id=class_id)
        except Exception as e:
            logger.error(f"获取班级失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级失败: {str(e)}")
    
    async def get_class_by_name(self, class_name: str) -> Optional[Class]:
        """根据名称获取班级"""
        try:
            return await Class.get_or_none(name=class_name)
        except Exception as e:
            logger.error(f"根据名称获取班级失败: {e}", exc_info=True)
            raise DatabaseException(f"根据名称获取班级失败: {str(e)}")
    
    async def get_classes(self, grade: str = None, college: str = None) -> List[Class]:
        """获取班级列表"""
        try:
            query = Class.all()
            if grade:
                query = query.filter(grade=grade)
            if college:
                query = query.filter(college=college)
            return await query.order_by('-created_at')
        except Exception as e:
            logger.error(f"获取班级列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级列表失败: {str(e)}")
    
    async def update_class(self, class_obj) -> bool:
        """更新班级"""
        try:
            await class_obj.save()
            logger.info(f"更新班级成功: {class_obj.id}")
            return True
        except Exception as e:
            logger.error(f"更新班级失败: {e}", exc_info=True)
            raise DatabaseException(f"更新班级失败: {str(e)}")
    
    async def delete_class(self, class_id: str) -> bool:
        """删除班级"""
        try:
            class_obj = await Class.get_or_none(id=class_id)
            if not class_obj:
                return False
            await class_obj.delete()
            logger.info(f"删除班级成功: {class_id}")
            return True
        except Exception as e:
            logger.error(f"删除班级失败: {e}", exc_info=True)
            raise DatabaseException(f"删除班级失败: {str(e)}")
    
    async def get_class_student(self, class_id: str, student_id: str) -> Optional[ClassStudent]:
        """获取班级学生关联"""
        try:
            return await ClassStudent.get_or_none(class_id=class_id, student_id=student_id)
        except Exception as e:
            logger.error(f"获取班级学生关联失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级学生关联失败: {str(e)}")
    
    async def add_student_to_class(self, class_id: str, student_id: str, class_student_id: str = None) -> ClassStudent:
        """添加学生到班级"""
        try:
            class_student = await ClassStudent.create(
                class_id=class_id,
                student_id=student_id
            )
            logger.info(f"添加学生到班级成功: {student_id} -> {class_id}")
            return class_student
        except IntegrityError:
            logger.error(f"学生已在班级中: {student_id} -> {class_id}")
            raise DatabaseException(f"学生已在班级中")
        except Exception as e:
            logger.error(f"添加学生到班级失败: {e}", exc_info=True)
            raise DatabaseException(f"添加学生到班级失败: {str(e)}")
    
    async def delete_class_student(self, class_student_id: int) -> bool:
        """删除班级学生关联"""
        try:
            class_student = await ClassStudent.get_or_none(id=class_student_id)
            if not class_student:
                return False
            await class_student.delete()
            logger.info(f"删除班级学生关联成功: {class_student_id}")
            return True
        except Exception as e:
            logger.error(f"删除班级学生关联失败: {e}", exc_info=True)
            raise DatabaseException(f"删除班级学生关联失败: {str(e)}")
    
    async def get_class_students(self, class_id: str) -> List[Dict[str, Any]]:
        """获取班级学生列表"""
        try:
            class_students = await ClassStudent.filter(class_id=class_id).all()
            result = []
            for cs in class_students:
                student = await Student.get_or_none(id=cs.student_id)
                if student:
                    result.append({
                        "id": cs.id,
                        "class_id": cs.class_id,
                        "student_id": student.id,
                        "student_name": student.name,
                        "student_college": student.college,
                        "student_major": student.major,
                        "student_grade": student.grade,
                        "created_at": cs.created_at
                    })
            return result
        except Exception as e:
            logger.error(f"获取班级学生列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级学生列表失败: {str(e)}")
    
    # 学业成绩相关操作
    async def create_academic_score(self, student_id: str, student_name: str,
                                    total_score: float = 0.0,
                                    semester: str = None, academic_year: str = None,
                                    **kwargs) -> AcademicScore:
        """创建学业成绩记录"""
        try:
            score = await AcademicScore.create(
                student_id=student_id,
                student_name=student_name,
                total_score=total_score,
                semester=semester,
                academic_year=academic_year,
                **kwargs
            )
            logger.info(f"创建学业成绩记录成功: {student_id} - {semester}")
            return score
        except IntegrityError as e:
            logger.error(f"创建学业成绩记录失败（已存在）: {student_id} - {semester}")
            raise DatabaseException(f"该学生在此学期的成绩记录已存在")
        except Exception as e:
            logger.error(f"创建学业成绩记录失败: {e}", exc_info=True)
            raise DatabaseException(f"创建学业成绩记录失败: {str(e)}")
    
    async def get_academic_score(self, score_id: int) -> Optional[AcademicScore]:
        """获取学业成绩记录"""
        try:
            return await AcademicScore.get_or_none(id=score_id).prefetch_related('student')
        except Exception as e:
            logger.error(f"获取学业成绩记录失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学业成绩记录失败: {str(e)}")
    
    async def get_academic_scores(self, student_id: str = None, semester: str = None,
                                 academic_year: str = None, class_name: str = None,
                                 limit: int = None, offset: int = None) -> List[AcademicScore]:
        """获取学业成绩记录列表"""
        try:
            query = AcademicScore.all()
            
            if student_id:
                query = query.filter(student_id=student_id)
            if semester:
                query = query.filter(semester=semester)
            if academic_year:
                query = query.filter(academic_year=academic_year)
            if class_name:
                query = query.filter(class_name=class_name)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return await query.prefetch_related('student').order_by('-created_at')
        except Exception as e:
            logger.error(f"获取学业成绩记录列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学业成绩记录列表失败: {str(e)}")
    
    async def update_academic_score(self, score_id: int, **kwargs) -> bool:
        """更新学业成绩记录"""
        try:
            score = await AcademicScore.get_or_none(id=score_id)
            if not score:
                return False
            
            await score.update_from_dict(kwargs)
            await score.save()
            logger.info(f"更新学业成绩记录成功: {score_id}")
            return True
        except DoesNotExist:
            logger.error(f"更新学业成绩记录失败，记录不存在: {score_id}")
            return False
        except Exception as e:
            logger.error(f"更新学业成绩记录失败: {e}", exc_info=True)
            raise DatabaseException(f"更新学业成绩记录失败: {str(e)}")
    
    async def delete_academic_score(self, score_id: int) -> bool:
        """删除学业成绩记录"""
        try:
            score = await AcademicScore.get_or_none(id=score_id)
            if not score:
                return False
            
            await score.delete()
            logger.info(f"删除学业成绩记录成功: {score_id}")
            return True
        except DoesNotExist:
            logger.error(f"删除学业成绩记录失败，记录不存在: {score_id}")
            return False
        except Exception as e:
            logger.error(f"删除学业成绩记录失败: {e}", exc_info=True)
            raise DatabaseException(f"删除学业成绩记录失败: {str(e)}")
    
    async def upsert_academic_score(self, student_id: str, semester: str, 
                                   academic_year: str, **kwargs) -> AcademicScore:
        """创建或更新学业成绩记录（如果已存在则更新）"""
        try:
            # 查找是否已存在
            score = await AcademicScore.get_or_none(
                student_id=student_id,
                semester=semester,
                academic_year=academic_year
            )
            
            if score:
                # 更新现有记录
                await score.update_from_dict(kwargs)
                await score.save()
                logger.info(f"更新学业成绩记录: {student_id} - {semester}")
            else:
                # 创建新记录
                score = await AcademicScore.create(
                    student_id=student_id,
                    semester=semester,
                    academic_year=academic_year,
                    **kwargs
                )
                logger.info(f"创建学业成绩记录: {student_id} - {semester}")
            
            return score
        except Exception as e:
            logger.error(f"创建/更新学业成绩记录失败: {e}", exc_info=True)
            raise DatabaseException(f"创建/更新学业成绩记录失败: {str(e)}")
    
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
    
    async def upsert_comprehensive_score(self, student_id: str, semester: str, 
                                        academic_year: str, **kwargs) -> ComprehensiveScore:
        """创建或更新综测成绩（如果已存在则更新）"""
        try:
            # 查找是否已存在
            score = await ComprehensiveScore.get_or_none(
                student_id=student_id,
                semester=semester,
                academic_year=academic_year
            )
            
            if score:
                # 更新现有记录
                await score.update_from_dict(kwargs)
                await score.save()
                logger.info(f"更新综测成绩: {student_id} - {semester}")
            else:
                # 创建新记录
                score = await ComprehensiveScore.create(
                    student_id=student_id,
                    semester=semester,
                    academic_year=academic_year,
                    **kwargs
                )
                logger.info(f"创建综测成绩: {student_id} - {semester}")
            
            return score
        except Exception as e:
            logger.error(f"创建/更新综测成绩失败: {e}", exc_info=True)
            raise DatabaseException(f"创建/更新综测成绩失败: {str(e)}")
    
    # 综测配置相关操作
    async def create_comprehensive_score_config(self, name: str, **kwargs) -> ComprehensiveScoreConfig:
        """创建综测配置"""
        try:
            config = await ComprehensiveScoreConfig.create(
                name=name,
                **kwargs
            )
            logger.info(f"创建综测配置成功: {name}")
            return config
        except Exception as e:
            logger.error(f"创建综测配置失败: {e}", exc_info=True)
            raise DatabaseException(f"创建综测配置失败: {str(e)}")
    
    async def get_comprehensive_score_config(self, config_id: int) -> Optional[ComprehensiveScoreConfig]:
        """获取综测配置"""
        try:
            return await ComprehensiveScoreConfig.get_or_none(id=config_id)
        except Exception as e:
            logger.error(f"获取综测配置失败: {e}", exc_info=True)
            raise DatabaseException(f"获取综测配置失败: {str(e)}")
    
    async def get_default_comprehensive_score_config(self) -> Optional[ComprehensiveScoreConfig]:
        """获取默认综测配置"""
        try:
            return await ComprehensiveScoreConfig.get_or_none(is_default=True, is_active=True)
        except Exception as e:
            logger.error(f"获取默认综测配置失败: {e}", exc_info=True)
            raise DatabaseException(f"获取默认综测配置失败: {str(e)}")
    
    async def get_comprehensive_score_configs(self, is_active: bool = None, 
                                             limit: int = None, offset: int = None) -> List[ComprehensiveScoreConfig]:
        """获取综测配置列表"""
        try:
            query = ComprehensiveScoreConfig.all()
            
            if is_active is not None:
                query = query.filter(is_active=is_active)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return await query.order_by('-created_at')
        except Exception as e:
            logger.error(f"获取综测配置列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取综测配置列表失败: {str(e)}")
    
    async def update_comprehensive_score_config(self, config_id: int, **kwargs) -> bool:
        """更新综测配置"""
        try:
            config = await ComprehensiveScoreConfig.get_or_none(id=config_id)
            if not config:
                return False
            
            # 如果设置为默认配置，先取消其他配置的默认状态
            if kwargs.get('is_default', False):
                await ComprehensiveScoreConfig.filter(is_default=True).update(is_default=False)
            
            await config.update_from_dict(kwargs)
            await config.save()
            logger.info(f"更新综测配置成功: {config_id}")
            return True
        except Exception as e:
            logger.error(f"更新综测配置失败: {e}", exc_info=True)
            raise DatabaseException(f"更新综测配置失败: {str(e)}")
    
    async def delete_comprehensive_score_config(self, config_id: int) -> bool:
        """删除综测配置"""
        try:
            config = await ComprehensiveScoreConfig.get_or_none(id=config_id)
            if not config:
                return False
            
            # 不允许删除默认配置
            if config.is_default:
                raise DatabaseException("不允许删除默认配置")
            
            await config.delete()
            logger.info(f"删除综测配置成功: {config_id}")
            return True
        except DatabaseException:
            raise
        except Exception as e:
            logger.error(f"删除综测配置失败: {e}", exc_info=True)
            raise DatabaseException(f"删除综测配置失败: {str(e)}")
    
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
    
    # ============================================================================
    # 证书相关操作
    # ============================================================================
    
    async def create_certificate(
        self,
        student_id: str,
        file_id: str,
        filename: str,
        file_path: Optional[str] = None,
        title: Optional[str] = None,
        level: Optional[str] = None,
        issuer: Optional[str] = None,
        issue_date: Optional[str] = None,
        raw_text: Optional[str] = None,
        category: str = "C",
        score: float = 0.0,
        classification_reason: Optional[str] = None,
        ocr_result: Optional[Dict[str, Any]] = None,
        certificate_info: Optional[Dict[str, Any]] = None,
        status: str = "pending"
    ) -> Certificate:
        """创建证书记录"""
        try:
            certificate = await Certificate.create(
                student_id=student_id,
                file_id=file_id,
                filename=filename,
                file_path=file_path,
                title=title,
                level=level,
                issuer=issuer,
                issue_date=issue_date,
                raw_text=raw_text,
                category=category,
                score=score,
                classification_reason=classification_reason,
                ocr_result=ocr_result,
                certificate_info=certificate_info,
                status=status
            )
            logger.info(f"创建证书记录成功: student_id={student_id}, title={title}")
            return certificate
        except Exception as e:
            logger.error(f"创建证书记录失败: {e}", exc_info=True)
            raise DatabaseException(f"创建证书记录失败: {str(e)}")
    
    async def get_certificates(
        self,
        student_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Certificate]:
        """获取证书列表"""
        try:
            query = Certificate.all()
            
            if student_id:
                query = query.filter(student_id=student_id)
            if category:
                query = query.filter(category=category)
            if status:
                query = query.filter(status=status)
            
            return await query.order_by('-created_at')
        except Exception as e:
            logger.error(f"获取证书列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取证书列表失败: {str(e)}")
    
    async def get_student_certificates_summary(
        self,
        student_id: str,
        status: str = "approved"
    ) -> Dict[str, float]:
        """获取学生证书汇总（A类和C类总分）"""
        try:
            certificates = await Certificate.filter(
                student_id=student_id,
                status=status
            ).all()
            
            a_total = sum(c.score for c in certificates if c.category == "A")
            c_total = sum(c.score for c in certificates if c.category == "C")
            
            return {
                "a_total_score": a_total,
                "c_total_score": c_total,
                "a_count": sum(1 for c in certificates if c.category == "A"),
                "c_count": sum(1 for c in certificates if c.category == "C"),
                "total_count": len(certificates)
            }
        except Exception as e:
            logger.error(f"获取学生证书汇总失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学生证书汇总失败: {str(e)}")
    
    async def update_certificate_status(
        self,
        certificate_id: int,
        status: str,
        reviewed_by: Optional[str] = None,
        review_comment: Optional[str] = None
    ) -> bool:
        """更新证书状态"""
        try:
            certificate = await Certificate.get_or_none(id=certificate_id)
            if not certificate:
                return False
            
            certificate.status = status
            if reviewed_by:
                certificate.reviewed_by = reviewed_by
            if review_comment:
                certificate.review_comment = review_comment
            certificate.reviewed_at = datetime.now()
            
            await certificate.save()
            logger.info(f"更新证书状态成功: id={certificate_id}, status={status}")
            return True
        except Exception as e:
            logger.error(f"更新证书状态失败: {e}", exc_info=True)
            raise DatabaseException(f"更新证书状态失败: {str(e)}")
    
    async def update_comprehensive_score_with_certificates(
        self,
        student_id: str,
        semester: str,
        academic_year: str
    ) -> bool:
        """根据证书更新综测成绩中的A类和C类分数"""
        try:
            # 获取证书汇总
            cert_summary = await self.get_student_certificates_summary(
                student_id=student_id,
                status="approved"
            )
            
            # 获取现有的综测成绩
            comp_scores = await self.get_comprehensive_scores(
                student_id=student_id,
                semester=semester,
                academic_year=academic_year
            )
            
            if comp_scores:
                # 更新现有记录
                comp_score = comp_scores[0]
                comp_score.a_total_score = cert_summary["a_total_score"]
                comp_score.c_total_score = cert_summary["c_total_score"]
                await comp_score.save()
                logger.info(f"更新综测成绩证书分数: student_id={student_id}")
            else:
                # 如果没有综测成绩记录，创建一个新的
                await self.upsert_comprehensive_score(
                    student_id=student_id,
                    semester=semester,
                    academic_year=academic_year,
                    a_total_score=cert_summary["a_total_score"],
                    b_total_score=0.0,
                    c_total_score=cert_summary["c_total_score"],
                    total_score=0.0,
                    remarks="仅证书分数"
                )
                logger.info(f"创建综测成绩记录（仅证书）: student_id={student_id}")
            
            return True
        except Exception as e:
            logger.error(f"更新综测成绩证书分数失败: {e}", exc_info=True)
            raise DatabaseException(f"更新综测成绩证书分数失败: {str(e)}")


# 创建全局数据库服务实例
db_service = DatabaseService()


def get_db_service() -> DatabaseService:
    """获取数据库服务实例"""
    return db_service