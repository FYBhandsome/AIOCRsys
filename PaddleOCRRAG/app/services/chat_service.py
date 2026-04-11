"""
聊天服务层
处理AI对话交流的业务逻辑
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator
from app.core.llm_manager import LLMManager
from app.core.cache import cache_manager
from app.core.logger import get_logger
from app.core.prompt_manager import PromptManager

logger = get_logger(__name__)


class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        """初始化聊天服务"""
        self._llm_manager = None
        self._vector_db = None
        self._prompt_manager = None
        self._cache = cache_manager.get_cache("chat", max_size=500, ttl=600)
    
    @property
    def llm_manager(self):
        """延迟加载LLM管理器"""
        if self._llm_manager is None:
            self._llm_manager = LLMManager()
        return self._llm_manager
    
    @property
    def vector_db(self):
        """延迟加载向量数据库"""
        if self._vector_db is None:
            from app.rag.vector_db.vector_db import get_vector_db
            self._vector_db = get_vector_db()
        return self._vector_db
    
    @property
    def prompt_manager(self):
        """延迟加载Prompt管理器"""
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager()
        return self._prompt_manager
    
    def _retrieve_context(self, question: str, top_k: int = 5) -> str:
        """检索相关上下文
        
        Args:
            question: 用户问题
            top_k: 检索结果数量
            
        Returns:
            格式化的上下文字符串
        """
        try:
            results = self.vector_db.search_relevant(
                query=question,
                top_k=top_k,
                similarity_threshold=0.65
            )
            
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            
            if not documents:
                logger.warning(f"未找到相关上下文: {question[:50]}")
                return ""
            
            context_parts = []
            for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
                category = meta.get("category", "未知类别") if meta else "未知类别"
                context_parts.append(f"[{i}] 类别: {category}\n内容: {doc}")
            
            context = "\n\n".join(context_parts)
            logger.info(f"检索到{len(documents)}条相关上下文")
            return context
            
        except Exception as e:
            logger.error(f"检索上下文失败: {str(e)}")
            return ""
    
    def chat(self, question: str, history: Optional[List[Dict]] = None, 
             use_cache: bool = True, use_optimized: bool = False, use_rag: bool = True) -> Dict[str, Any]:
        """处理聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            use_cache: 是否使用缓存
            use_optimized: 是否使用优化模式
            use_rag: 是否使用RAG检索
            
        Returns:
            聊天响应字典
        """
        try:
            history = history or []
            
            if use_cache:
                cache_key = self._generate_cache_key(question, history, use_rag)
                cached_result = self._cache.get(cache_key)
                if cached_result:
                    logger.debug(f"聊天缓存命中: {question[:50]}...")
                    return cached_result
            
            context = ""
            if use_rag:
                context = self._retrieve_context(question)
            
            if context:
                prompt = self.prompt_manager.get_chat_prompt(query=question, context=context)
                logger.info(f"使用RAG增强提示词，上下文长度: {len(context)}")
            else:
                prompt = question
                logger.warning(f"未使用RAG，直接传递问题")
            
            response = self.llm_manager.generate(prompt)
            
            result = {
                "question": question,
                "answer": response,
                "timestamp": datetime.now().isoformat(),
                "cached": False,
                "used_rag": use_rag and bool(context),
                "context_length": len(context) if context else 0
            }
            
            if use_cache:
                self._cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"对话处理失败: {str(e)}")
            raise
    
    def chat_stream(self, question: str, history: Optional[List[Dict]] = None, use_rag: bool = True) -> Generator[str, None, None]:
        """处理流式聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            use_rag: 是否使用RAG检索
            
        Yields:
            流式响应数据
        """
        try:
            history = history or []
            
            context = ""
            if use_rag:
                context = self._retrieve_context(question)
            
            if context:
                prompt = self.prompt_manager.get_chat_prompt(query=question, context=context)
                logger.info(f"流式对话使用RAG增强，上下文长度: {len(context)}")
            else:
                prompt = question
                logger.warning(f"流式对话未使用RAG")
            
            full_response = ""
            
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat(), 'used_rag': use_rag and bool(context)}, ensure_ascii=False)}\n\n"
            
            for chunk in self.llm_manager.generate_stream(prompt):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'end', 'full_response': full_response, 'timestamp': datetime.now().isoformat(), 'context_length': len(context) if context else 0}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式对话处理失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    async def chat_async(self, question: str, history: Optional[List[Dict]] = None, 
                         use_cache: bool = True, use_rag: bool = True) -> Dict[str, Any]:
        """异步处理聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            use_cache: 是否使用缓存
            use_rag: 是否使用RAG检索
            
        Returns:
            聊天响应字典
        """
        try:
            history = history or []
            
            if use_cache:
                cache_key = self._generate_cache_key(question, history, use_rag)
                cached_result = self._cache.get(cache_key)
                if cached_result:
                    logger.debug(f"聊天缓存命中: {question[:50]}...")
                    return cached_result
            
            context = ""
            if use_rag:
                context = self._retrieve_context(question)
            
            if context:
                prompt = self.prompt_manager.get_chat_prompt(query=question, context=context)
                logger.info(f"异步对话使用RAG增强，上下文长度: {len(context)}")
            else:
                prompt = question
                logger.warning(f"异步对话未使用RAG")
            
            response = await self.llm_manager.generate_async(prompt)
            
            result = {
                "question": question,
                "answer": response,
                "timestamp": datetime.now().isoformat(),
                "cached": False,
                "used_rag": use_rag and bool(context),
                "context_length": len(context) if context else 0
            }
            
            if use_cache:
                self._cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"异步对话处理失败: {str(e)}")
            raise
    
    async def chat_stream_async(self, question: str, history: Optional[List[Dict]] = None, use_rag: bool = True) -> AsyncGenerator[str, None]:
        """异步流式聊天请求
        
        Args:
            question: 用户问题
            history: 对话历史
            use_rag: 是否使用RAG检索
            
        Yields:
            流式响应数据
        """
        try:
            history = history or []
            
            context = ""
            if use_rag:
                context = self._retrieve_context(question)
            
            if context:
                prompt = self.prompt_manager.get_chat_prompt(query=question, context=context)
                logger.info(f"异步流式对话使用RAG增强，上下文长度: {len(context)}")
            else:
                prompt = question
                logger.warning(f"异步流式对话未使用RAG")
            
            full_response = ""
            
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat(), 'used_rag': use_rag and bool(context)}, ensure_ascii=False)}\n\n"
            
            async for chunk in self.llm_manager.generate_stream_async(prompt):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'end', 'full_response': full_response, 'timestamp': datetime.now().isoformat(), 'context_length': len(context) if context else 0}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"异步流式对话处理失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    def _generate_cache_key(self, question: str, history: List[Dict], use_rag: bool = True) -> str:
        """生成缓存键"""
        import hashlib
        key_data = json.dumps({
            "question": question,
            "history": history,
            "use_rag": use_rag
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self._cache.get_stats()
    
    def clear_cache(self) -> None:
        """清空聊天缓存"""
        self._cache.clear()
        logger.info("聊天缓存已清空")
