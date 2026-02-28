#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础仓储层模块
实现数据访问层的抽象和基础实现
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from tortoise.models import Model
from tortoise.queryset import QuerySet

ModelType = TypeVar("ModelType", bound=Model)


class BaseRepository(ABC, Generic[ModelType]):
    """基础仓储抽象类"""
    
    def __init__(self, model: type[ModelType]):
        self.model = model
    
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """创建记录"""
        return await self.model.create(**data)
    
    async def get_by_id(self, id: Union[int, str]) -> Optional[ModelType]:
        """根据ID获取记录"""
        return await self.model.get_or_none(id=id)
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """根据字段获取记录"""
        return await self.model.get_or_none(**{field: value})
    
    async def get_all(
        self,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> List[ModelType]:
        """获取所有记录"""
        queryset = self.model.all()
        
        if filters:
            queryset = queryset.filter(**filters)
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        if offset:
            queryset = queryset.offset(offset)
        
        if limit:
            queryset = queryset.limit(limit)
        
        return await queryset.all()
    
    async def update(self, id: Union[int, str], data: Dict[str, Any]) -> Optional[ModelType]:
        """更新记录"""
        record = await self.get_by_id(id)
        if record:
            for key, value in data.items():
                setattr(record, key, value)
            await record.save()
        return record
    
    async def delete(self, id: Union[int, str]) -> bool:
        """删除记录"""
        record = await self.get_by_id(id)
        if record:
            await record.delete()
            return True
        return False
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """统计记录数"""
        queryset = self.model.all()
        if filters:
            queryset = queryset.filter(**filters)
        return await queryset.count()
    
    async def exists(self, filters: Dict[str, Any]) -> bool:
        """检查记录是否存在"""
        return await self.model.filter(**filters).exists()
    
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """批量创建"""
        return await self.model.bulk_create([self.model(**data) for data in data_list])
    
    async def bulk_update(self, records: List[ModelType], fields: List[str]) -> int:
        """批量更新"""
        return await self.model.bulk_update(records, fields)


class StudentRepository(BaseRepository):
    """学生仓储"""
    
    def __init__(self):
        from app.models.tortoise_models import Student
        super().__init__(Student)
    
    async def get_by_student_id(self, student_id: str):
        """根据学号获取学生"""
        return await self.get_by_field("id", student_id)
    
    async def get_by_class(self, class_name: str):
        """根据班级获取学生列表"""
        return await self.get_all(filters={"class_name": class_name})
    
    async def search(self, keyword: str, limit: int = 20):
        """搜索学生"""
        return await self.model.filter(
            name__contains=keyword
        ).limit(limit).all()


class AcademicScoreRepository(BaseRepository):
    """学业成绩仓储"""
    
    def __init__(self):
        from app.models.tortoise_models import AcademicScore
        super().__init__(AcademicScore)
    
    async def get_student_scores(
        self,
        student_id: str,
        academic_year: str = None,
        semester: str = None
    ):
        """获取学生成绩"""
        filters = {"student_id": student_id}
        if academic_year:
            filters["academic_year"] = academic_year
        if semester:
            filters["semester"] = semester
        
        return await self.get_all(filters=filters, order_by="-created_at")
    
    async def get_class_scores(
        self,
        class_name: str,
        academic_year: str,
        semester: str
    ):
        """获取班级成绩"""
        return await self.model.filter(
            student__class_name=class_name,
            academic_year=academic_year,
            semester=semester
        ).prefetch_related("student").all()


class ComprehensiveScoreRepository(BaseRepository):
    """综测成绩仓储"""
    
    def __init__(self):
        from app.models.tortoise_models import ComprehensiveScore
        super().__init__(ComprehensiveScore)
    
    async def get_student_score(
        self,
        student_id: str,
        academic_year: str,
        semester: str
    ):
        """获取学生综测成绩"""
        return await self.model.get_or_none(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester
        )
    
    async def get_class_ranking(
        self,
        class_name: str,
        academic_year: str,
        semester: str
    ):
        """获取班级排名"""
        return await self.model.filter(
            class_name=class_name,
            academic_year=academic_year,
            semester=semester
        ).order_by("-total_score").all()


class CertificateRepository(BaseRepository):
    """证书仓储"""
    
    def __init__(self):
        from app.models.tortoise_models import Certificate
        super().__init__(Certificate)
    
    async def get_student_certificates(
        self,
        student_id: str,
        status: str = None
    ):
        """获取学生证书"""
        filters = {"student_id": student_id, "is_valid": True}
        if status:
            filters["status"] = status
        
        return await self.get_all(filters=filters, order_by="-created_at")
    
    async def get_pending_certificates(self, limit: int = 100):
        """获取待审核证书"""
        return await self.get_all(
            filters={"status": "pending", "is_valid": True},
            order_by="created_at",
            limit=limit
        )


class FileMetadataRepository(BaseRepository):
    """文件元数据仓储"""
    
    def __init__(self):
        from app.models.tortoise_models import FileMetadata
        super().__init__(FileMetadata)
    
    async def get_by_file_id(self, file_id: str):
        """根据文件ID获取记录"""
        return await self.get_by_field("file_id", file_id)
    
    async def get_user_files(
        self,
        owner_id: str,
        file_type: str = None
    ):
        """获取用户文件列表"""
        filters = {"owner_id": owner_id, "status": "active"}
        if file_type:
            filters["file_type"] = file_type
        
        return await self.get_all(filters=filters, order_by="-created_at")


# 仓储实例工厂
_repositories = {}

def get_repository(repo_class: type) -> BaseRepository:
    """获取仓储实例"""
    if repo_class not in _repositories:
        _repositories[repo_class] = repo_class()
    return _repositories[repo_class]

def get_student_repository() -> StudentRepository:
    return get_repository(StudentRepository)

def get_academic_score_repository() -> AcademicScoreRepository:
    return get_repository(AcademicScoreRepository)

def get_comprehensive_score_repository() -> ComprehensiveScoreRepository:
    return get_repository(ComprehensiveScoreRepository)

def get_certificate_repository() -> CertificateRepository:
    return get_repository(CertificateRepository)

def get_file_metadata_repository() -> FileMetadataRepository:
    return get_repository(FileMetadataRepository)
