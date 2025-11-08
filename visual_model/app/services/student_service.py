#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生服务 - 重构版本
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger
from app.core.exceptions import (
    StudentNotFoundException,
    ValidationException,
    DatabaseException
)
from app.models.student import (
    Student, StudentCreate, StudentUpdate, StudentResponse,
    Activity, ActivityCreate, ActivityUpdate,
    ScoreRecord, ScoreRecordCreate, ScoreRecordUpdate,
    StudentProfile, StudentAnalysis, ClassRankingResponse
)
from app.services.database_tortoise import get_db_service

class StudentService:
    """学生服务"""
    
    def __init__(self):
        """初始化学生服务"""
        self.db_service = get_db_service()
        logger.info("学生服务初始化完成")
    
    async def create_student(self, student_data: StudentCreate) -> Student:
        """创建学生"""
        try:
            # 验证学生数据
            if not student_data.id or not student_data.name:
                raise ValidationException("学生ID和姓名不能为空")
            
            # 检查学生是否已存在
            existing_student = await self.get_student(student_data.id)
            if existing_student:
                raise ValidationException(f"学生ID {student_data.id} 已存在")
            
            # 创建学生记录
            student = Student(
                id=student_data.id,
                name=student_data.name,
                class_name=student_data.class_name,
                grade=student_data.grade,
                major=student_data.major,
                college=student_data.college,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            await self.db_service.save_student(student)
            logger.info(f"创建学生成功: {student.id}")
            return student
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"创建学生失败: {e}", exc_info=True)
            raise DatabaseException(f"创建学生失败: {str(e)}")
    
    async def get_student(self, student_id: str) -> Optional[Student]:
        """获取学生信息"""
        try:
            student = await self.db_service.get_student(student_id)
            if not student:
                raise StudentNotFoundException(student_id)
            return student
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取学生信息失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学生信息失败: {str(e)}")
    
    async def update_student(self, student_id: str, student_data: StudentUpdate) -> Student:
        """更新学生信息"""
        try:
            # 获取现有学生
            student = await self.get_student(student_id)
            
            # 准备更新数据
            update_data = {}
            if student_data.name is not None:
                update_data["name"] = student_data.name
            if student_data.class_name is not None:
                update_data["class_name"] = student_data.class_name
            if student_data.grade is not None:
                update_data["grade"] = student_data.grade
            if student_data.major is not None:
                update_data["major"] = student_data.major
            if student_data.college is not None:
                update_data["college"] = student_data.college
            
            # 更新时间戳
            update_data["updated_at"] = datetime.now()
            
            # 保存到数据库
            success = await self.db_service.update_student(student_id, **update_data)
            if not success:
                raise DatabaseException(f"更新学生信息失败: {student_id}")
            
            # 获取更新后的学生信息
            updated_student = await self.get_student(student_id)
            logger.info(f"更新学生信息成功: {student_id}")
            return updated_student
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"更新学生信息失败: {e}", exc_info=True)
            raise DatabaseException(f"更新学生信息失败: {str(e)}")
    
    async def delete_student(self, student_id: str) -> bool:
        """删除学生"""
        try:
            # 获取学生
            await self.get_student(student_id)
            
            # 删除学生
            await self.db_service.delete_student(student_id)
            logger.info(f"删除学生成功: {student_id}")
            return True
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除学生失败: {e}", exc_info=True)
            raise DatabaseException(f"删除学生失败: {str(e)}")
    
    
    async def get_students(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """获取学生列表"""
        try:
            students = await self.db_service.get_students(offset=skip, limit=limit)
            return students
            
        except Exception as e:
            logger.error(f"获取学生列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学生列表失败: {str(e)}")
    
    async def create_activity(self, activity_data: ActivityCreate) -> Activity:
        """创建学生活动"""
        try:
            # 验证学生是否存在
            await self.get_student(activity_data.student_id)
            
            # 创建活动记录
            activity = Activity(
                id=str(datetime.now().timestamp()),
                student_id=activity_data.student_id,
                name=activity_data.name,
                type=activity_data.type,
                date=activity_data.date,
                location=activity_data.location,
                description=activity_data.description,
                score=activity_data.score,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            await self.db_service.save_activity(activity)
            logger.info(f"创建学生活动成功: {activity.id}")
            return activity
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"创建学生活动失败: {e}", exc_info=True)
            raise DatabaseException(f"创建学生活动失败: {str(e)}")
    
    async def get_activities(self, student_id: str) -> List[Activity]:
        """获取学生活动列表"""
        try:
            # 验证学生是否存在
            await self.get_student(student_id)
            
            # 获取活动列表
            activities = await self.db_service.get_activities(student_id)
            return activities
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取学生活动列表失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学生活动列表失败: {str(e)}")
    
    async def update_activity(self, activity_id: str, activity_data: ActivityUpdate) -> Activity:
        """更新学生活动"""
        try:
            # 获取现有活动
            activity = await self.db_service.get_activity(activity_id)
            if not activity:
                raise ValidationException(f"活动不存在: {activity_id}")
            
            # 更新字段
            if activity_data.name is not None:
                activity.name = activity_data.name
            if activity_data.type is not None:
                activity.type = activity_data.type
            if activity_data.date is not None:
                activity.date = activity_data.date
            if activity_data.location is not None:
                activity.location = activity_data.location
            if activity_data.description is not None:
                activity.description = activity_data.description
            if activity_data.score is not None:
                activity.score = activity_data.score
            
            # 保存到数据库
            await self.db_service.update_activity(activity)
            logger.info(f"更新学生活动成功: {activity.id}")
            return activity
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"更新学生活动失败: {e}", exc_info=True)
            raise DatabaseException(f"更新学生活动失败: {str(e)}")
    
    async def delete_activity(self, activity_id: str) -> bool:
        """删除学生活动"""
        try:
            # 获取活动
            activity = await self.db_service.get_activity(activity_id)
            if not activity:
                raise ValidationException(f"活动不存在: {activity_id}")
            
            # 删除活动
            await self.db_service.delete_activity(activity_id)
            logger.info(f"删除学生活动成功: {activity_id}")
            return True
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"删除学生活动失败: {e}", exc_info=True)
            raise DatabaseException(f"删除学生活动失败: {str(e)}")
    
    async def create_score_record(self, score_data: ScoreRecordCreate) -> ScoreRecord:
        """创建学生分数记录"""
        try:
            # 验证学生是否存在
            await self.get_student(score_data.student_id)
            
            # 创建分数记录
            score_record = ScoreRecord(
                id=str(datetime.now().timestamp()),
                student_id=score_data.student_id,
                subject=score_data.subject,
                score=score_data.score,
                max_score=score_data.max_score,
                exam_date=score_data.exam_date,
                exam_type=score_data.exam_type,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            await self.db_service.save_score_record(score_record)
            logger.info(f"创建学生分数记录成功: {score_record.id}")
            return score_record
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"创建学生分数记录失败: {e}", exc_info=True)
            raise DatabaseException(f"创建学生分数记录失败: {str(e)}")
    
    async def get_score_records(self, student_id: str) -> List[ScoreRecord]:
        """获取学生分数记录"""
        try:
            # 验证学生是否存在
            await self.get_student(student_id)
            
            # 获取分数记录
            score_records = await self.db_service.get_score_records(student_id)
            return score_records
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取学生分数记录失败: {e}", exc_info=True)
            raise DatabaseException(f"获取学生分数记录失败: {str(e)}")
    
    
    async def analyze_student(self, student_id: str) -> StudentAnalysis:
        """分析学生数据"""
        try:
            # 获取学生信息
            student = await self.get_student(student_id)
            
            # 获取学生活动
            activities = await self.get_activities(student_id)
            
            # 获取学生分数记录
            score_records = await self.get_score_records(student_id)
            
            # 计算统计数据
            total_score = sum(record.score for record in score_records)
            average_score = total_score / len(score_records) if score_records else 0
            highest_score = max(record.score for record in score_records) if score_records else 0
            lowest_score = min(record.score for record in score_records) if score_records else 0
            
            # 按科目统计
            subject_scores = {}
            for record in score_records:
                if record.subject not in subject_scores:
                    subject_scores[record.subject] = []
                subject_scores[record.subject].append(record.score)
            
            subject_averages = {}
            for subject, scores in subject_scores.items():
                subject_averages[subject] = sum(scores) / len(scores)
            
            # 创建分析结果
            analysis = StudentAnalysis(
                student_id=student_id,
                student_name=student.name,
                class_name=student.class_name,
                total_activities=len(activities),
                total_score_records=len(score_records),
                total_score=total_score,
                average_score=average_score,
                highest_score=highest_score,
                lowest_score=lowest_score,
                subject_averages=subject_averages,
                analysis_date=datetime.now()
            )
            
            logger.info(f"分析学生数据成功: {student_id}")
            return analysis
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"分析学生数据失败: {e}", exc_info=True)
            raise DatabaseException(f"分析学生数据失败: {str(e)}")
    


# 全局学生服务实例
student_service = StudentService()

def get_student_service() -> StudentService:
    """获取学生服务实例"""
    return student_service