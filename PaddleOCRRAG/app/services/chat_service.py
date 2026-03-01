"""
聊天服务层
处理AI对话交流的业务逻辑
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator
from app.core.llm_manager import LLMManager
from app.core.cache import cached, async_cached, cache_manager
from app.core.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        """初始化聊天服务"""
        self._llm_manager = None
        self._cache = cache_manager.get_cache("chat", max_size=500, ttl=600)
    
    @property
    def llm_manager(self):
        """延迟加载LLM管理器"""
        if self._llm_manager is None:
            self._llm_manager = LLMManager()
        return self._llm_manager
    
    def chat(self, question: str, history: Optional[List[Dict]] = None, 
             use_cache: bool = True, use_optimized: bool = False) -> Dict[str, Any]:
        """处理聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            use_cache: 是否使用缓存
            use_optimized: 是否使用优化模式
            
        Returns:
            聊天响应字典
        """
        try:
            history = history or []
            
            if use_cache:
                cache_key = self._generate_cache_key(question, history)
                cached_result = self._cache.get(cache_key)
                if cached_result:
                    logger.debug(f"聊天缓存命中: {question[:50]}...")
                    return cached_result
            
            response = self.llm_manager.generate(question)
            
            result = {
                "question": question,
                "answer": response,
                "timestamp": datetime.now().isoformat(),
                "cached": False
            }
            
            if use_cache:
                self._cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"对话处理失败: {str(e)}")
            raise
    
    def chat_stream(self, question: str, history: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """处理流式聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            
        Yields:
            流式响应数据
        """
        try:
            history = history or []
            full_response = ""
            
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            for chunk in self.llm_manager.generate_stream(question):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'end', 'full_response': full_response, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式对话处理失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    async def chat_async(self, question: str, history: Optional[List[Dict]] = None, 
                         use_cache: bool = True) -> Dict[str, Any]:
        """异步处理聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            use_cache: 是否使用缓存
            
        Returns:
            聊天响应字典
        """
        try:
            history = history or []
            
            if use_cache:
                cache_key = self._generate_cache_key(question, history)
                cached_result = self._cache.get(cache_key)
                if cached_result:
                    logger.debug(f"聊天缓存命中: {question[:50]}...")
                    return cached_result
            
            response = await self.llm_manager.generate_async(question)
            
            result = {
                "question": question,
                "answer": response,
                "timestamp": datetime.now().isoformat(),
                "cached": False
            }
            
            if use_cache:
                self._cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"异步对话处理失败: {str(e)}")
            raise
    
    async def chat_stream_async(self, question: str, history: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        """异步流式聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            
        Yields:
            流式响应数据
        """
        try:
            history = history or []
            full_response = ""
            
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            async for chunk in self.llm_manager.generate_stream_async(question):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'end', 'full_response': full_response, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"异步流式对话处理失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    def _generate_cache_key(self, question: str, history: List[Dict]) -> str:
        """生成缓存键"""
        import hashlib
        key_data = json.dumps({
            "question": question,
            "history": history
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self._cache.get_stats()
    
    def clear_cache(self) -> None:
        """清空聊天缓存"""
        self._cache.clear()
        logger.info("聊天缓存已清空")
