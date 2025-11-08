#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
班级服务 - 重构版本
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger
from app.core.exceptions import (
    ClassNotFoundException,
    StudentNotFoundException,
    ValidationException,
    DatabaseException
)
from app.models.class_ import (
    Class, ClassCreate, ClassUpdate, ClassResponse,
    ClassProfile, ClassStudentListResponse, ClassStatisticsResponse
)
from app.models.student import StudentUpdate
from app.services.database_tortoise import get_db_service
from app.services.student_service import get_student_service

class ClassService:
    """班级服务"""
    
    def __init__(self):
        """初始化班级服务"""
        self.db_service = get_db_service()
        self.student_service = get_student_service()
        logger.info("班级服务初始化完成")
    
    async def create_class(self, class_data: ClassCreate) -> Class:
        """创建班级"""
        try:
            # 验证班级数据
            if not class_data.name:
                raise ValidationException("班级名称不能为空")
            
            # 检查班级是否已存在
            existing_class = await self.get_class_by_name(class_data.name)
            if existing_class:
                raise ValidationException(f"班级名称 {class_data.name} 已存在")
            
            # 创建班级记录
            class_obj = Class(
                id=str(datetime.now().timestamp()),
                name=class_data.name,
                grade=class_data.grade,
                major=class_data.major,
                college=class_data.college,
                description=class_data.description,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            await self.db_service.save_class(class_obj)
            logger.info(f"创建班级成功: {class_obj.id}")
            return class_obj
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"创建班级失败: {e}", exc_info=True)
            raise DatabaseException(f"创建班级失败: {str(e)}")
    
    async def get_class(self, class_id: str) -> Optional[Class]:
        """获取班级信息"""
        try:
            class_obj = await self.db_service.get_class(class_id)
            if not class_obj:
                raise ClassNotFoundException(class_id)
            return class_obj
            
        except ClassNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取班级信息失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级信息失败: {str(e)}")
    
    async def get_class_by_name(self, class_name: str) -> Optional[Class]:
        """根据名称获取班级信息"""
        try:
            class_obj = await self.db_service.get_class_by_name(class_name)
            return class_obj
            
        except Exception as e:
            logger.error(f"根据名称获取班级信息失败: {e}", exc_info=True)
            raise DatabaseException(f"根据名称获取班级信息失败: {str(e)}")
    
    async def update_class(self, class_id: str, class_data: ClassUpdate) -> Class:
        """更新班级信息"""
        try:
            # 获取现有班级
            class_obj = await self.get_class(class_id)
            
            # 更新字段
            if class_data.name is not None:
                class_obj.name = class_data.name
            if class_data.grade is not None:
                class_obj.grade = class_data.grade
            if class_data.major is not None:
                class_obj.major = class_data.major
            if class_data.college is not None:
                class_obj.college = class_data.college
            if class_data.description is not None:
                class_obj.description = class_data.description
            
            class_obj.updated_at = datetime.now()
            
            # 保存到数据库
            await self.db_service.update_class(class_obj)
            logger.info(f"更新班级信息成功: {class_obj.id}")
            return class_obj
            
        except ClassNotFoundException:
            raise
        except Exception as e:
            logger.error(f"更新班级信息失败: {e}", exc_info=True)
            raise DatabaseException(f"更新班级信息失败: {str(e)}")
    
    async def delete_class(self, class_id: str) -> bool:
        """删除班级"""
        try:
            # 获取班级
            await self.get_class(class_id)
            
            # 删除班级
            await self.db_service.delete_class(class_id)
            logger.info(f"删除班级成功: {class_id}")
            return True
            
        except ClassNotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除班级失败: {e}", exc_info=True)
            raise DatabaseException(f"删除班级失败: {str(e)}")
    
    async def get_classes(self, grade: Optional[str] = None, college: Optional[str] = None) -> List[Class]:
        """获取班级列表"""
        try:
            classes = await self.db_service.get_classes(grade, college)
            return classes
            
        except Exception as e:
            logger.error(f"获取班级列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级列表失败: {str(e)}")
    
    async def add_student_to_class(self, class_id: str, student_id: str) -> bool:
        """添加学生到班级"""
        try:
            # 验证班级是否存在
            await self.get_class(class_id)
            
            # 验证学生是否存在
            await self.student_service.get_student(student_id)
            
            # 检查学生是否已在班级中
            existing_class_student = await self.db_service.get_class_student(class_id, student_id)
            if existing_class_student:
                raise ValidationException(f"学生 {student_id} 已在班级 {class_id} 中")
            
            # 创建班级学生记录
            class_student_id = str(datetime.now().timestamp())
            await self.db_service.add_student_to_class(class_id, student_id, class_student_id)
            
            # 更新学生的班级信息
            await self.student_service.update_student(student_id, StudentUpdate(class_name=(await self.get_class(class_id)).name))
            
            logger.info(f"添加学生到班级成功: {student_id} -> {class_id}")
            return True
            
        except (ClassNotFoundException, StudentNotFoundException):
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"添加学生到班级失败: {e}", exc_info=True)
            raise DatabaseException(f"添加学生到班级失败: {str(e)}")
    
    async def remove_student_from_class(self, class_id: str, student_id: str) -> bool:
        """从班级中移除学生"""
        try:
            # 验证班级是否存在
            await self.get_class(class_id)
            
            # 验证学生是否存在
            await self.student_service.get_student(student_id)
            
            # 获取班级学生记录
            class_student = await self.db_service.get_class_student(class_id, student_id)
            if not class_student:
                raise ValidationException(f"学生 {student_id} 不在班级 {class_id} 中")
            
            # 删除班级学生记录
            await self.db_service.delete_class_student(class_student.id)
            
            # 更新学生的班级信息
            await self.student_service.update_student(student_id, StudentUpdate(class_name=""))
            
            logger.info(f"从班级中移除学生成功: {student_id} -> {class_id}")
            return True
            
        except (ClassNotFoundException, StudentNotFoundException):
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"从班级中移除学生失败: {e}", exc_info=True)
            raise DatabaseException(f"从班级中移除学生失败: {str(e)}")
    
    async def get_class_students(self, class_id: str) -> List[Dict[str, Any]]:
        """获取班级学生列表"""
        try:
            # 验证班级是否存在
            await self.get_class(class_id)
            
            # 获取班级学生列表
            class_students = await self.db_service.get_class_students(class_id)
            return class_students
            
        except ClassNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取班级学生列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级学生列表失败: {str(e)}")
    
    async def get_class_statistics(self, class_id: str) -> ClassStatisticsResponse:
        """获取班级统计信息"""
        try:
            # 验证班级是否存在
            class_obj = await self.get_class(class_id)
            
            # 获取班级学生列表
            class_students = await self.get_class_students(class_id)
            
            # 统计学生数量
            student_count = len(class_students)
            
            # 统计各科目平均分
            subject_scores = {}
            total_scores = {}
            
            for class_student in class_students:
                # 获取学生分数记录
                score_records = await self.student_service.get_score_records(class_student["id"])
                
                for record in score_records:
                    if record.subject not in subject_scores:
                        subject_scores[record.subject] = []
                        total_scores[record.subject] = 0
                    
                    subject_scores[record.subject].append(record.score)
                    total_scores[record.subject] += record.score
            
            # 计算各科目平均分
            subject_averages = {}
            for subject, scores in subject_scores.items():
                subject_averages[subject] = total_scores[subject] / len(scores)
            
            # 统计活动数量
            activity_count = 0
            for class_student in class_students:
                activities = await self.student_service.get_activities(class_student["id"])
                activity_count += len(activities)
            
            # 获取最高分学生
            top_student = {}
            if class_students:
                # 简化处理，取第一个学生作为示例
                first_student_id = class_students[0]["id"]
                student = await self.student_service.get_student(first_student_id)
                top_student = {
                    "id": student.id,
                    "name": student.name,
                    "total_score": 0  # 这里应该计算总分，简化处理
                }
            
            # 创建统计结果
            statistics = ClassStatisticsResponse(
                class_id=class_id,
                class_name=class_obj.name,
                student_count=student_count,
                average_score=sum(subject_averages.values()) / len(subject_averages) if subject_averages else 0,
                top_student=top_student,
                subject_averages=subject_averages,
                updated_at=datetime.now()
            )
            
            logger.info(f"获取班级统计信息成功: {class_id}")
            return statistics
            
        except ClassNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取班级统计信息失败: {e}", exc_info=True)
            raise DatabaseException(f"获取班级统计信息失败: {str(e)}")


# 全局班级服务实例
class_service = ClassService()

def get_class_service() -> ClassService:
    """获取班级服务实例"""
    return class_service