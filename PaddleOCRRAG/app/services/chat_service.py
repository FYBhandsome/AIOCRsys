"""
聊天服务层
处理AI对话交流的业务逻辑
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Generator
from app.core.llm_manager import llm_manager

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        """初始化聊天服务"""
        self.llm_manager = llm_manager
    
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
            
            # 使用llm_manager进行对话
            response = self.llm_manager.generate(question)
            
            return {
                "question": question,
                "answer": response,
                "timestamp": datetime.now().isoformat()
            }
            
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
            
            # 这里简化处理，实际应用中应该使用真正的流式响应
            response = self.llm_manager.generate(question)
            yield f"data: {json.dumps({'type': 'chunk', 'content': response}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式对话处理失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
