#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础服务层模块
实现业务逻辑层的抽象和基础实现
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
import logging
import json
from datetime import datetime

from app.core.logger import get_logger
from app.core.base_repository import BaseRepository
from app.core.api_response import ResponseBuilder, ApiException, ResponseCode

RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)
logger = get_logger(__name__)


class BaseService(ABC, Generic[RepositoryType]):
    """基础服务抽象类"""
    
    def __init__(self, repository: RepositoryType):
        self.repository = repository
        self.logger = get_logger(self.__class__.__name__)
    
    def _log_operation(self, operation: str, data: Any = None):
        """记录操作日志"""
        log_data = {
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
        if data:
            log_data["data"] = data
        
        self.logger.info(f"[{self.__class__.__name__}] {json.dumps(log_data, ensure_ascii=False)[:500]}")
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建记录"""
        self._log_operation("create", {"data": data})
        
        try:
            record = await self.repository.create(data)
            return ResponseBuilder.success(
                data=self._to_dict(record),
                message="创建成功"
            )
        except Exception as e:
            self.logger.error(f"创建失败: {e}", exc_info=True)
            raise ApiException(
                code=ResponseCode.OPERATION_FAILED,
                message=f"创建失败: {str(e)}"
            )
    
    async def get_by_id(self, id: int) -> Dict[str, Any]:
        """根据ID获取记录"""
        self._log_operation("get_by_id", {"id": id})
        
        record = await self.repository.get_by_id(id)
        if not record:
            raise ApiException(
                code=ResponseCode.DATA_NOT_FOUND,
                message="记录不存在"
            )
        
        return ResponseBuilder.success(data=self._to_dict(record))
    
    async def get_all(
        self,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> Dict[str, Any]:
        """获取所有记录"""
        self._log_operation("get_all", {"filters": filters})
        
        records = await self.repository.get_all(
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        
        return ResponseBuilder.success(
            data=[self._to_dict(r) for r in records]
        )
    
    async def update(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新记录"""
        self._log_operation("update", {"id": id, "data": data})
        
        record = await self.repository.update(id, data)
        if not record:
            raise ApiException(
                code=ResponseCode.DATA_NOT_FOUND,
                message="记录不存在"
            )
        
        return ResponseBuilder.success(
            data=self._to_dict(record),
            message="更新成功"
        )
    
    async def delete(self, id: int) -> Dict[str, Any]:
        """删除记录"""
        self._log_operation("delete", {"id": id})
        
        success = await self.repository.delete(id)
        if not success:
            raise ApiException(
                code=ResponseCode.DATA_NOT_FOUND,
                message="记录不存在"
            )
        
        return ResponseBuilder.success(message="删除成功")
    
    async def count(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """统计记录数"""
        count = await self.repository.count(filters)
        return ResponseBuilder.success(data={"count": count})
    
    def _to_dict(self, record) -> Dict[str, Any]:
        """将模型转换为字典"""
        if hasattr(record, "__dict__"):
            result = {}
            for key, value in record.__dict__.items():
                if not key.startswith("_"):
                    if isinstance(value, datetime):
                        result[key] = value.isoformat()
                    else:
                        result[key] = value
            return result
        return dict(record) if record else {}


class StudentService(BaseService):
    """学生服务"""
    
    def __init__(self):
        from app.core.base_repository import get_student_repository
        super().__init__(get_student_repository())
    
    async def get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """获取学生档案"""
        self._log_operation("get_student_profile", {"student_id": student_id})
        
        student = await self.repository.get_by_student_id(student_id)
        if not student:
            raise ApiException(
                code=ResponseCode.DATA_NOT_FOUND,
                message="学生不存在"
            )
        
        return ResponseBuilder.success(data=self._to_dict(student))
    
    async def search_students(self, keyword: str, limit: int = 20) -> Dict[str, Any]:
        """搜索学生"""
        self._log_operation("search_students", {"keyword": keyword})
        
        students = await self.repository.search(keyword, limit)
        return ResponseBuilder.success(
            data=[self._to_dict(s) for s in students]
        )
    
    async def get_class_students(self, class_name: str) -> Dict[str, Any]:
        """获取班级学生列表"""
        self._log_operation("get_class_students", {"class_name": class_name})
        
        students = await self.repository.get_by_class(class_name)
        return ResponseBuilder.success(
            data=[self._to_dict(s) for s in students]
        )


class AcademicScoreService(BaseService):
    """学业成绩服务"""
    
    def __init__(self):
        from app.core.base_repository import get_academic_score_repository
        super().__init__(get_academic_score_repository())
    
    async def get_student_scores(
        self,
        student_id: str,
        academic_year: str = None,
        semester: str = None
    ) -> Dict[str, Any]:
        """获取学生成绩"""
        self._log_operation("get_student_scores", {
            "student_id": student_id,
            "academic_year": academic_year,
            "semester": semester
        })
        
        scores = await self.repository.get_student_scores(
            student_id, academic_year, semester
        )
        
        return ResponseBuilder.success(
            data=[self._to_dict(s) for s in scores]
        )
    
    async def get_class_scores(
        self,
        class_name: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """获取班级成绩"""
        self._log_operation("get_class_scores", {
            "class_name": class_name,
            "academic_year": academic_year,
            "semester": semester
        })
        
        scores = await self.repository.get_class_scores(
            class_name, academic_year, semester
        )
        
        return ResponseBuilder.success(
            data=[self._to_dict(s) for s in scores]
        )


class ComprehensiveScoreService(BaseService):
    """综测成绩服务"""
    
    def __init__(self):
        from app.core.base_repository import get_comprehensive_score_repository
        super().__init__(get_comprehensive_score_repository())
    
    async def get_student_score(
        self,
        student_id: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """获取学生综测成绩"""
        self._log_operation("get_student_score", {
            "student_id": student_id,
            "academic_year": academic_year,
            "semester": semester
        })
        
        score = await self.repository.get_student_score(
            student_id, academic_year, semester
        )
        
        if not score:
            raise ApiException(
                code=ResponseCode.DATA_NOT_FOUND,
                message="综测成绩不存在"
            )
        
        return ResponseBuilder.success(data=self._to_dict(score))
    
    async def get_class_ranking(
        self,
        class_name: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """获取班级排名"""
        self._log_operation("get_class_ranking", {
            "class_name": class_name,
            "academic_year": academic_year,
            "semester": semester
        })
        
        rankings = await self.repository.get_class_ranking(
            class_name, academic_year, semester
        )
        
        return ResponseBuilder.success(
            data=[self._to_dict(r) for r in rankings]
        )
    
    async def calculate_score(
        self,
        student_id: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """计算综测成绩"""
        self._log_operation("calculate_score", {
            "student_id": student_id,
            "academic_year": academic_year,
            "semester": semester
        })
        
        from app.services.comprehensive_score_service import ComprehensiveScoreService
        service = ComprehensiveScoreService()
        result = await service.calculate_student_score(student_id, academic_year, semester)
        
        if result.get('success'):
            return ResponseBuilder.success(
                message="综测成绩计算完成",
                data=result
            )
        else:
            return ResponseBuilder.error(
                message=result.get('message', '计算失败'),
                data=result
            )


class CertificateService(BaseService):
    """证书服务"""
    
    def __init__(self):
        from app.core.base_repository import get_certificate_repository
        super().__init__(get_certificate_repository())
    
    async def get_student_certificates(
        self,
        student_id: str,
        status: str = None
    ) -> Dict[str, Any]:
        """获取学生证书"""
        self._log_operation("get_student_certificates", {
            "student_id": student_id,
            "status": status
        })
        
        certificates = await self.repository.get_student_certificates(
            student_id, status
        )
        
        return ResponseBuilder.success(
            data=[self._to_dict(c) for c in certificates]
        )
    
    async def get_pending_certificates(self, limit: int = 100) -> Dict[str, Any]:
        """获取待审核证书"""
        self._log_operation("get_pending_certificates", {"limit": limit})
        
        certificates = await self.repository.get_pending_certificates(limit)
        
        return ResponseBuilder.success(
            data=[self._to_dict(c) for c in certificates]
        )
    
    async def approve_certificate(self, certificate_id: int, reviewer: str) -> Dict[str, Any]:
        """审核通过证书"""
        self._log_operation("approve_certificate", {
            "certificate_id": certificate_id,
            "reviewer": reviewer
        })
        
        return await self.update(certificate_id, {
            "status": "approved",
            "reviewed_by": reviewer,
            "reviewed_at": datetime.now()
        })
    
    async def reject_certificate(
        self,
        certificate_id: int,
        reviewer: str,
        reason: str
    ) -> Dict[str, Any]:
        """审核拒绝证书"""
        self._log_operation("reject_certificate", {
            "certificate_id": certificate_id,
            "reviewer": reviewer,
            "reason": reason
        })
        
        return await self.update(certificate_id, {
            "status": "rejected",
            "reviewed_by": reviewer,
            "reviewed_at": datetime.now(),
            "review_comment": reason
        })


class FileService(BaseService):
    """文件服务"""
    
    def __init__(self):
        from app.core.base_repository import get_file_metadata_repository
        super().__init__(get_file_metadata_repository())
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """获取文件信息"""
        self._log_operation("get_file_info", {"file_id": file_id})
        
        file_meta = await self.repository.get_by_file_id(file_id)
        if not file_meta:
            raise ApiException(
                code=ResponseCode.FILE_NOT_FOUND,
                message="文件不存在"
            )
        
        return ResponseBuilder.success(data=self._to_dict(file_meta))
    
    async def get_user_files(
        self,
        owner_id: str,
        file_type: str = None
    ) -> Dict[str, Any]:
        """获取用户文件列表"""
        self._log_operation("get_user_files", {
            "owner_id": owner_id,
            "file_type": file_type
        })
        
        files = await self.repository.get_user_files(owner_id, file_type)
        
        return ResponseBuilder.success(
            data=[self._to_dict(f) for f in files]
        )


# 服务实例工厂
_services = {}

def get_service(service_class: type) -> BaseService:
    """获取服务实例"""
    if service_class not in _services:
        _services[service_class] = service_class()
    return _services[service_class]

def get_student_service() -> StudentService:
    return get_service(StudentService)

def get_academic_score_service() -> AcademicScoreService:
    return get_service(AcademicScoreService)

def get_comprehensive_score_service() -> ComprehensiveScoreService:
    return get_service(ComprehensiveScoreService)

def get_certificate_service() -> CertificateService:
    return get_service(CertificateService)

def get_file_service() -> FileService:
    return get_service(FileService)
