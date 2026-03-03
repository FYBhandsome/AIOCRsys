"""
依赖注入容器模块

此模块提供统一的依赖注入机制，负责管理应用核心组件的创建、缓存和依赖关系。
使用单例模式确保每个组件在应用生命周期内只被初始化一次，避免资源浪费和状态不一致。
"""
from functools import lru_cache
from typing import Dict, Any, TypeVar, Callable, Optional
import logging
import traceback

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyContainer:
    """
    依赖注入容器
    
    集中管理所有核心组件的生命周期，确保单例模式和正确的依赖关系。
    使用更健壮的实例创建和缓存机制，提供清晰的错误处理。
    """
    
    def __init__(self):
        """初始化依赖注入容器"""
        self._instances: Dict[str, Any] = {}
        self._initialization_status: Dict[str, bool] = {}
    
    def _get_or_create_instance(self, instance_name: str, factory: Callable[[], T]) -> T:
        """
        获取或创建实例的通用方法
        
        Args:
            instance_name: 实例名称
            factory: 创建实例的工厂函数
            
        Returns:
            组件实例
            
        Raises:
            Exception: 当实例创建失败时
        """
        if instance_name not in self._instances:
            try:
                self._initialization_status[instance_name] = False
                instance = factory()
                self._instances[instance_name] = instance
                self._initialization_status[instance_name] = True
            except Exception as e:
                self._initialization_status[instance_name] = False
                logger.error(f"Failed to initialize {instance_name}: {str(e)}")
                logger.error(traceback.format_exc())
                raise RuntimeError(f"Failed to initialize {instance_name}: {str(e)}") from e
        return self._instances[instance_name]
    
    @lru_cache(maxsize=1)
    def get_config_manager(self):
        """获取配置管理器实例"""
        from app.core.config_manager import config_manager
        return config_manager
    
    @lru_cache(maxsize=1)
    def get_document_manager(self):
        """获取文档管理器实例"""
        from app.core.document_manager import DocumentManager
        return self._get_or_create_instance('document_manager', DocumentManager)
    
    @lru_cache(maxsize=1)
    def get_llm_manager(self):
        """获取LLM管理器实例"""
        from app.core.llm_manager import llm_manager
        return llm_manager
    
    @lru_cache(maxsize=1)
    def get_prompt_manager(self):
        """获取Prompt管理器实例"""
        from app.core.prompt_manager import prompt_manager
        return prompt_manager
    
    @lru_cache(maxsize=1)
    def get_certificate_service(self):
        """获取证书服务实例"""
        from app.services.certificate_service import CertificateService
        return self._get_or_create_instance('certificate_service', CertificateService)
    
    @lru_cache(maxsize=1)
    def get_chat_service(self):
        """获取聊天服务实例"""
        from app.services.chat_service import ChatService
        return self._get_or_create_instance('chat_service', ChatService)
    
    @lru_cache(maxsize=1)
    def get_document_service(self):
        """获取文档服务实例"""
        from app.services.document_service import DocumentService
        return self._get_or_create_instance('document_service', DocumentService)
    
    @lru_cache(maxsize=1)
    def get_system_service(self):
        """获取系统服务实例"""
        from app.services.system_service import SystemService
        return self._get_or_create_instance('system_service', SystemService)
    
    @lru_cache(maxsize=1)
    def get_vector_db(self):
        """获取向量数据库实例"""
        from app.rag.vector_db.vector_db import get_vector_db
        return get_vector_db()
    
    def get_initialization_status(self, instance_name: str) -> Optional[bool]:
        """
        获取组件初始化状态
        
        Args:
            instance_name: 实例名称
            
        Returns:
            bool: 初始化状态，None表示未开始初始化
        """
        return self._initialization_status.get(instance_name)
    
    def clear_instance(self, instance_name: str) -> bool:
        """
        清除指定实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            bool: 是否成功清除
        """
        if instance_name in self._instances:
            del self._instances[instance_name]
            if instance_name in self._initialization_status:
                del self._initialization_status[instance_name]
            return True
        return False
    
    def clear_all_instances(self):
        """清除所有实例"""
        self._instances.clear()
        self._initialization_status.clear()
