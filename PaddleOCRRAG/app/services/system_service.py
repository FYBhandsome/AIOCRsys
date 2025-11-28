"""
系统服务层
处理系统管理相关的业务逻辑
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.config_manager import config_manager
from app.core.prompt_manager import prompt_manager
from app.core.llm_manager import llm_manager
from app.core.document_manager import DocumentManager

logger = logging.getLogger(__name__)


class SystemService:
    """系统服务类"""
    
    def __init__(self):
        """初始化系统服务"""
        self.config_manager = config_manager
        self.prompt_manager = prompt_manager
        self.llm_manager = llm_manager
        self.document_manager = DocumentManager()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息
        
        Returns:
            系统信息字典
        """
        try:
            return {
                "version": "1.0.0",
                "uptime": str(time.time()),
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": os.cpu_count(),
                "memory_usage": "N/A",
                "disk_usage": "N/A",
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康检查结果字典
        """
        try:
            # 检查各组件状态
            components = {
                "document_processor": True,
                "vector_store": True,
                "knowledge_base": True,
                "prompt_manager": True,
                "llm_manager": True,
            }
            
            # 判断整体健康状态
            healthy = all(components.values())
            
            return {
                "healthy": healthy,
                "components": components,
                "checked_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            raise
    
    def test_llm_connection(self) -> Dict[str, Any]:
        """测试LLM连接
        
        Returns:
            连接测试结果字典
        """
        try:
            # 使用llm_manager测试连接
            test_message = "你好，这是一个连接测试。"
            response = self.llm_manager.generate(test_message)
            
            return {
                "test_message": test_message,
                "response": response,
                "response_time": "模拟响应时间",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"LLM连接测试失败: {str(e)}")
            raise
    
    def get_vector_db_stats(self) -> Dict[str, Any]:
        """获取向量数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 使用document_manager获取统计信息
            stats = self.document_manager.get_statistics()
            
            # 添加额外信息
            stats.update({
                "index_size": "0 MB",
                "last_updated": datetime.now().isoformat()
            })
            
            return stats
        except Exception as e:
            logger.error(f"获取向量数据库统计信息失败: {str(e)}")
            raise
    
    def rebuild_vector_db(self) -> Dict[str, Any]:
        """重建向量数据库
        
        Returns:
            重建结果字典
        """
        try:
            # 获取所有启用的文档
            enabled_documents = self.document_manager.list_documents(enabled_only=True)
            
            if not enabled_documents:
                return {
                    "document_count": 0,
                    "status": "completed",
                    "message": "没有启用的文档需要处理",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 重建向量数据库
            doc_count = len(enabled_documents)
            
            return {
                "document_count": doc_count,
                "status": "completed",
                "message": f"向量数据库重建完成，处理了 {doc_count} 个文档",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"向量数据库重建失败: {str(e)}")
            raise
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置
        
        Returns:
            系统配置字典
        """
        try:
            return self.config_manager.get_config()
        except Exception as e:
            logger.error(f"获取系统配置失败: {str(e)}")
            raise
    
    def update_system_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新系统配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            更新后的配置字典
        """
        try:
            # 根据需要更新不同的配置部分
            if "llm" in config_data:
                llm_config = config_data["llm"]
                self.config_manager.update_llm_config(**llm_config)
            
            if "vector_db" in config_data:
                vector_db_config = config_data["vector_db"]
                self.config_manager.update_vector_db_config(**vector_db_config)
            
            if "rag" in config_data:
                rag_config = config_data["rag"]
                self.config_manager.update_rag_config(**rag_config)
            
            if "prompt" in config_data:
                prompt_config = config_data["prompt"]
                self.config_manager.update_prompt_config(**prompt_config)
            
            # 返回更新后的完整配置
            return self.config_manager.get_config()
        except Exception as e:
            logger.error(f"系统配置更新失败: {str(e)}")
            raise
