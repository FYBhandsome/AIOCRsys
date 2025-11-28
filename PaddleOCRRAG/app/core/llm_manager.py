"""
统一的LLM管理模块
支持多种LLM提供商的统一接口
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
import logging
from app.core.config_manager import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """LLM提供商基类"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        pass


class XunfeiSparkLLM(LLMProvider):
    """讯飞星火大模型实现"""
    
    def __init__(self):
        """初始化讯飞星火大模型"""
        self.api_key = settings.XUNFEI_API_KEY
        self.api_secret = settings.XUNFEI_API_SECRET
        self.app_id = settings.XUNFEI_APP_ID  # 使用MODEL_ID作为APP_ID
        self.api_url = settings.XUNFEI_API_URL
        self.model_id = settings.XUNFEI_MODEL_ID
        self.temperature = settings.XUNFEI_TEMPERATURE
        self.max_tokens = settings.XUNFEI_MAX_TOKENS
        
        # 检查配置是否完整
        # 根据用户说明，API_KEY就是XUNFEI_API_KEY，APP_ID就是XUNFEI_MODEL_ID
        # 只检查必要的配置项
        self.enabled = settings.USE_XUNFEI_LLM and all([
            self.api_key, self.app_id, self.api_url, self.model_id
        ])
        
        if not self.enabled:
            logger.info("讯飞星火大模型配置不完整，已禁用")
    
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        return self.enabled
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not self.enabled:
            return "讯飞星火大模型不可用，请检查配置"
        
        try:
            # 构建请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model_id,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens)
            }
            
            # 发送请求
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"讯飞星火API请求失败: {response.status_code}, {response.text}")
                return f"API请求失败: {response.status_code}"
                
        except Exception as e:
            logger.error(f"讯飞星火大模型调用失败: {str(e)}")
            return f"模型调用失败: {str(e)}"


class RuleMatchingEngine:
    """规则匹配引擎"""
    
    def __init__(self):
        """初始化规则匹配引擎"""
        self.rules = []
        self.load_rules()
    
    def load_rules(self):
        """加载规则"""
        try:
            # 这里可以从文件或数据库加载规则
            # 暂时使用空规则列表
            self.rules = []
            logger.info("规则匹配引擎初始化完成")
        except Exception as e:
            logger.error(f"规则加载失败: {str(e)}")
            self.rules = []
    
    def match(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """匹配规则"""
        try:
            # 这里实现规则匹配逻辑
            # 暂时返回默认结果
            return {
                "matched": False,
                "rule": None,
                "confidence": 0.0,
                "result": "未匹配到任何规则"
            }
        except Exception as e:
            logger.error(f"规则匹配失败: {str(e)}")
            return {
                "matched": False,
                "rule": None,
                "confidence": 0.0,
                "result": f"规则匹配失败: {str(e)}"
            }


class LLMManager:
    """LLM管理器"""
    
    def __init__(self):
        """初始化LLM管理器"""
        self.providers = {}
        self.rule_engine = RuleMatchingEngine()
        self._init_providers()
    
    def _init_providers(self):
        """初始化LLM提供商"""
        # 初始化讯飞星火大模型
        xunfei_llm = XunfeiSparkLLM()
        if xunfei_llm.is_available():
            self.providers["xunfei"] = xunfei_llm
            logger.info("讯飞星火大模型已启用")
        else:
            logger.info("讯飞星火大模型未启用")
    
    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """获取LLM提供商"""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """列出所有可用的提供商"""
        return list(self.providers.keys())
    
    def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """生成文本"""
        # 如果指定了提供商，使用指定的提供商
        if provider and provider in self.providers:
            return self.providers[provider].generate(prompt, **kwargs)
        
        # 如果没有指定提供商，尝试使用第一个可用的提供商
        if self.providers:
            first_provider = next(iter(self.providers.values()))
            return first_provider.generate(prompt, **kwargs)
        
        # 如果没有可用的提供商，使用规则引擎
        rule_result = self.rule_engine.match(prompt)
        return rule_result.get("result", "没有可用的LLM提供商")
    
    def is_available(self) -> bool:
        """检查是否有可用的提供商"""
        return len(self.providers) > 0
    
    def get_provider_status(self) -> Dict[str, Any]:
        """获取提供商状态"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "available": provider.is_available(),
                "type": provider.__class__.__name__
            }
        
        # 设置默认提供商
        if self.providers:
            default_provider = next(iter(self.providers.keys()))
            status["default"] = default_provider
        else:
            status["default"] = None
            
        return status
    
    def test_connection(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """测试连接"""
        try:
            test_prompt = "你好，请回复'连接成功'"
            response = self.generate(test_prompt, provider)
            
            return {
                "success": True,
                "message": "连接测试成功",
                "response": response,
                "provider": provider or "default"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}",
                "provider": provider or "default"
            }


# 创建全局LLM管理器实例
llm_manager = LLMManager()