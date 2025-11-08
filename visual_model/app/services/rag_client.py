#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG综测计算系统HTTP客户端
"""
from typing import Dict, Any, List, Optional
import httpx
from pathlib import Path

from app.core.logger import logger
from config import settings


class RAGClient:
    """RAG系统HTTP客户端"""
    
    def __init__(self, base_url: Optional[str] = None):
        """初始化RAG客户端
        
        Args:
            base_url: RAG系统基础URL（默认从配置读取）
        """
        self.base_url = base_url or getattr(settings, 'RAG_BASE_URL', 'http://localhost:8000')
        self.api_prefix = "/api/v1"
        self.timeout = 30.0
        logger.info(f"RAG客户端初始化: {self.base_url}")
    
    async def calculate_score(
        self,
        certificate_text: str,
        student_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """计算综测加分
        
        Args:
            certificate_text: 证书文本信息
            student_info: 学生信息（可选）
            
        Returns:
            加分计算结果
        """
        url = f"{self.base_url}{self.api_prefix}/calculate-score"
        data = {
            "certificate_text": certificate_text,
            "student_info": student_info or {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"调用RAG计算加分失败: {e}", exc_info=True)
            raise
    
    async def chat(
        self,
        message: str,
        use_rag: bool = True,
        chat_history: Optional[List[Dict[str, str]]] = None,
        student_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """AI对话
        
        Args:
            message: 用户消息
            use_rag: 是否使用RAG检索
            chat_history: 聊天历史
            student_info: 学生信息
            
        Returns:
            AI回复结果
        """
        url = f"{self.base_url}{self.api_prefix}/chat"
        data = {
            "message": message,
            "use_rag": use_rag,
            "chat_history": chat_history or [],
            "student_info": student_info or {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"调用RAG对话失败: {e}", exc_info=True)
            raise
    
    async def upload_document(
        self,
        file_path: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """上传规则文档
        
        Args:
            file_path: 文件路径
            description: 文档描述
            
        Returns:
            上传结果
        """
        url = f"{self.base_url}{self.api_prefix}/documents/upload"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
                    data = {'description': description}
                    response = await client.post(url, files=files, data=data)
                    response.raise_for_status()
                    return response.json()
        except Exception as e:
            logger.error(f"上传RAG文档失败: {e}", exc_info=True)
            raise
    
    async def list_documents(self, enabled_only: bool = False) -> Dict[str, Any]:
        """获取文档列表
        
        Args:
            enabled_only: 是否只返回启用的文档
            
        Returns:
            文档列表
        """
        url = f"{self.base_url}{self.api_prefix}/documents"
        params = {"enabled_only": enabled_only}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取RAG文档列表失败: {e}", exc_info=True)
            raise
    
    async def update_document_status(
        self,
        doc_id: str,
        enabled: bool
    ) -> Dict[str, Any]:
        """更新文档状态
        
        Args:
            doc_id: 文档ID
            enabled: 是否启用
            
        Returns:
            更新结果
        """
        url = f"{self.base_url}{self.api_prefix}/documents/{doc_id}/status"
        data = {"enabled": enabled}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"更新RAG文档状态失败: {e}", exc_info=True)
            raise
    
    async def delete_document(
        self,
        doc_id: str,
        delete_file: bool = False
    ) -> Dict[str, Any]:
        """删除文档
        
        Args:
            doc_id: 文档ID
            delete_file: 是否删除物理文件
            
        Returns:
            删除结果
        """
        url = f"{self.base_url}{self.api_prefix}/documents/{doc_id}"
        params = {"delete_file": delete_file}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"删除RAG文档失败: {e}", exc_info=True)
            raise
    
    async def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        url = f"{self.base_url}{self.api_prefix}/llm-config"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取LLM配置失败: {e}", exc_info=True)
            raise
    
    async def update_llm_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """更新LLM配置"""
        url = f"{self.base_url}{self.api_prefix}/llm-config"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(url, json=config)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"更新LLM配置失败: {e}", exc_info=True)
            raise
    
    async def test_llm_connection(self) -> Dict[str, Any]:
        """测试LLM连接"""
        url = f"{self.base_url}{self.api_prefix}/llm-config/test"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"测试LLM连接失败: {e}", exc_info=True)
            raise
    
    async def reset_llm_config(self) -> Dict[str, Any]:
        """重置LLM配置"""
        url = f"{self.base_url}{self.api_prefix}/llm-config/reset"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"重置LLM配置失败: {e}", exc_info=True)
            raise
    
    async def validate_llm_config(self) -> Dict[str, Any]:
        """验证LLM配置"""
        url = f"{self.base_url}{self.api_prefix}/llm-config/validate"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"验证LLM配置失败: {e}", exc_info=True)
            raise
    
    # ============================================================================
    # Prompt管理
    # ============================================================================
    
    async def get_prompts(self) -> Dict[str, Any]:
        """获取Prompt配置"""
        url = f"{self.base_url}{self.api_prefix}/prompts"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取Prompt配置失败: {e}", exc_info=True)
            raise
    
    async def update_prompts(self, prompts: Dict[str, Any]) -> Dict[str, Any]:
        """更新Prompt配置
        
        Args:
            prompts: Prompt配置（system_prompt, user_prompt, chat_system_prompt）
            
        Returns:
            更新结果
        """
        url = f"{self.base_url}{self.api_prefix}/prompts"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(url, json=prompts)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"更新Prompt配置失败: {e}", exc_info=True)
            raise
    
    async def reset_prompts(self) -> Dict[str, Any]:
        """重置Prompt配置为默认值"""
        url = f"{self.base_url}{self.api_prefix}/prompts/reset"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"重置Prompt配置失败: {e}", exc_info=True)
            raise
    
    # ============================================================================
    # 向量数据库管理
    # ============================================================================
    
    async def get_vector_db_stats(self) -> Dict[str, Any]:
        """获取向量数据库统计信息"""
        url = f"{self.base_url}{self.api_prefix}/vector-db/stats"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取向量数据库统计失败: {e}", exc_info=True)
            raise
    
    async def reset_vector_db(
        self,
        confirm: bool = True,
        rebuild: bool = False
    ) -> Dict[str, Any]:
        """重置向量数据库
        
        Args:
            confirm: 确认重置
            rebuild: 是否立即重建
            
        Returns:
            重置结果
        """
        url = f"{self.base_url}{self.api_prefix}/vector-db/reset"
        data = {
            "confirm": confirm,
            "rebuild": rebuild
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"重置向量数据库失败: {e}", exc_info=True)
            raise
    
    async def rebuild_vector_db(self) -> Dict[str, Any]:
        """重建向量数据库"""
        url = f"{self.base_url}{self.api_prefix}/vector-db/rebuild"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"重建向量数据库失败: {e}", exc_info=True)
            raise
    
    # ============================================================================
    # 系统信息
    # ============================================================================
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        url = f"{self.base_url}{self.api_prefix}/stats"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}", exc_info=True)
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        url = f"{self.base_url}{self.api_prefix}/health"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"健康检查失败: {e}", exc_info=True)
            raise
    
    # ============================================================================
    # 批量文档上传
    # ============================================================================
    
    async def batch_upload_documents(
        self,
        file_paths: List[str],
        description: str = ""
    ) -> Dict[str, Any]:
        """批量上传文档
        
        Args:
            file_paths: 文件路径列表
            description: 统一描述
            
        Returns:
            批量上传结果
        """
        url = f"{self.base_url}{self.api_prefix}/documents/batch-upload"
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = []
                for file_path in file_paths:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        files.append(('files', (Path(file_path).name, content, 'application/octet-stream')))
                
                data = {'description': description} if description else {}
                response = await client.post(url, files=files, data=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"批量上传文档失败: {e}", exc_info=True)
            raise


# 全局单例
_rag_client_instance: Optional[RAGClient] = None


def get_rag_client() -> RAGClient:
    """获取RAG客户端实例（单例）"""
    global _rag_client_instance
    
    if _rag_client_instance is None:
        _rag_client_instance = RAGClient()
    
    return _rag_client_instance

