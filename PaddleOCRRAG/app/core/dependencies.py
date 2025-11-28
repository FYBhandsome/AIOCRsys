"""
依赖注入容器模块

此模块提供统一的依赖注入机制，负责管理应用核心组件的创建、缓存和依赖关系。
使用单例模式确保每个组件在应用生命周期内只被初始化一次，避免资源浪费和状态不一致。
"""
from functools import lru_cache
from typing import Dict, Any, TypeVar, Callable, Optional
from app.core.config_manager import config_manager
from app.core.document_manager import DocumentManager
from app.core.llm_manager import llm_manager
from app.core.prompt_manager import prompt_manager
from app.services.certificate_service import CertificateService
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.system_service import SystemService

T = TypeVar('T')


class DependencyContainer:
    """
    依赖注入容器
    
    集中管理所有核心组件的生命周期，确保单例模式和正确的依赖关系。
    使用更健壮的实例创建和缓存机制，提供清晰的错误处理。
    """
    
    def __init__(self):
        """初始化依赖注入容器"""
        # 存储已创建的实例
        self._instances: Dict[str, Any] = {}
        # 记录组件初始化状态
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
                # 标记为初始化中
                self._initialization_status[instance_name] = False
                # 创建实例
                instance = factory()
                # 存储实例
                self._instances[instance_name] = instance
                # 标记为初始化完成
                self._initialization_status[instance_name] = True
            except Exception as e:
                # 记录初始化失败
                self._initialization_status[instance_name] = False
                raise RuntimeError(f"Failed to initialize {instance_name}: {str(e)}") from e
        return self._instances[instance_name]
    
    @lru_cache(maxsize=1)
    def get_config_manager(self):
        """
        获取配置管理器实例
        
        Returns:
            配置管理器单例
        """
        return config_manager
    
    @lru_cache(maxsize=1)
    def get_document_manager(self) -> DocumentManager:
        """
        获取文档管理器实例
        
        Returns:
            文档管理器单例
        """
        return self._get_or_create_instance('document_manager', DocumentManager)
    
    @lru_cache(maxsize=1)
    def get_llm_manager(self):
        """
        获取LLM管理器实例
        
        Returns:
            LLM管理器单例
        """
        return llm_manager
    
    @lru_cache(maxsize=1)
    def get_prompt_manager(self):
        """
        获取Prompt管理器实例
        
        Returns:
            Prompt管理器单例
        """
        return prompt_manager
    
    @lru_cache(maxsize=1)
    def get_certificate_service(self) -> CertificateService:
        """
        获取证书服务实例
        
        Returns:
            证书服务单例
        """
        return self._get_or_create_instance('certificate_service', CertificateService)
    
    @lru_cache(maxsize=1)
    def get_chat_service(self) -> ChatService:
        """
        获取聊天服务实例
        
        Returns:
            聊天服务单例
        """
        return self._get_or_create_instance('chat_service', ChatService)
    
    @lru_cache(maxsize=1)
    def get_document_service(self) -> DocumentService:
        """
        获取文档服务实例
        
        Returns:
            文档服务单例
        """
        return self._get_or_create_instance('document_service', DocumentService)
    
    @lru_cache(maxsize=1)
    def get_system_service(self) -> SystemService:
        """
        获取系统服务实例
        
        Returns:
            系统服务单例
        """
        return self._get_or_create_instance('system_service', SystemService)
    
    def get_initialization_status(self, instance_name: str) -> Optional[bool]:
        """
        获取组件初始化状态
        
        Args:
            instance_name: 组件名称
            
        Returns:
            初始化状态，None表示未初始化
        """
        return self._initialization_status.get(instance_name)
    
    def clear_instance(self, instance_name: str) -> bool:
        """
        清除指定实例（用于测试或重新初始化）
        
        Args:
            instance_name: 实例名称
            
        Returns:
            是否成功清除
        """
        if instance_name in self._instances:
            del self._instances[instance_name]
            if instance_name in self._initialization_status:
                del self._initialization_status[instance_name]
            return True
        return False


# 创建全局容器实例
container = DependencyContainer()


# FastAPI依赖函数
def get_config_manager():
    """
    FastAPI依赖：获取配置管理器
    
    Returns:
        配置管理器实例，用于访问应用配置
    """
    return container.get_config_manager()


def get_document_manager() -> DocumentManager:
    """
    FastAPI依赖：获取文档管理器
    
    Returns:
        DocumentManager实例，用于处理文档的存储和检索
    """
    return container.get_document_manager()


def get_llm_manager():
    """
    FastAPI依赖：获取LLM管理器
    
    Returns:
        LLM管理器实例，用于与语言模型交互
    """
    return container.get_llm_manager()


def get_prompt_manager():
    """
    FastAPI依赖：获取Prompt管理器
    
    Returns:
        Prompt管理器实例，用于管理和获取提示模板
    """
    return container.get_prompt_manager()


def get_certificate_service() -> CertificateService:
    """
    FastAPI依赖：获取证书服务
    
    Returns:
        CertificateService实例，用于处理证书加分计算逻辑
    """
    return container.get_certificate_service()


def get_chat_service() -> ChatService:
    """
    FastAPI依赖：获取聊天服务
    
    Returns:
        ChatService实例，用于处理AI对话和问答
    """
    return container.get_chat_service()


def get_document_service() -> DocumentService:
    """
    FastAPI依赖：获取文档服务
    
    Returns:
        DocumentService实例，用于处理文档上传和管理
    """
    return container.get_document_service()


def get_system_service() -> SystemService:
    """
    FastAPI依赖：获取系统服务
    
    Returns:
        SystemService实例，用于系统健康检查和管理功能
    """
    return container.get_system_service()
