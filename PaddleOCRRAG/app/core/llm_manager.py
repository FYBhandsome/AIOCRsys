"""
统一的LLM管理模块
支持多种LLM提供商的统一接口，包括流式响应支持
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Generator, AsyncGenerator
from abc import ABC, abstractmethod
import logging
from app.core.config_manager import settings
from app.core.exceptions import LLMException
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """LLM提供商基类"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """流式生成文本"""
        pass
    
    @abstractmethod
    async def generate_async(self, prompt: str, **kwargs) -> str:
        """异步生成文本"""
        pass
    
    @abstractmethod
    async def generate_stream_async(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        pass


class XunfeiSparkLLM(LLMProvider):
    """讯飞星火大模型实现 - 支持OpenAI兼容格式"""
    
    def __init__(self):
        """初始化讯飞星火大模型"""
        self.api_key = settings.XUNFEI_API_KEY
        self.api_secret = settings.XUNFEI_API_SECRET
        self.app_id = settings.XUNFEI_APP_ID
        self.api_url = settings.XUNFEI_API_URL
        self.model_id = settings.XUNFEI_MODEL_ID
        self.temperature = settings.XUNFEI_TEMPERATURE
        self.max_tokens = settings.XUNFEI_MAX_TOKENS
        
        self.enabled = settings.USE_XUNFEI_LLM and all([
            self.api_key, self.app_id, self.api_url, self.model_id
        ])
        
        if not self.enabled:
            logger.info("讯飞星火大模型配置不完整，已禁用")
        else:
            logger.info("讯飞星火大模型已启用")
    
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        return self.enabled
    
    def _build_request_data(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """构建请求数据"""
        return {
            "model": kwargs.get("model", self.model_id),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": kwargs.get("stream", False)
        }
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头 - 使用Bearer Token认证"""
        # 讯飞MaaS平台使用 api_key:api_secret 组合作为Bearer Token
        if self.api_secret:
            auth_token = f"{self.api_key}:{self.api_secret}"
        else:
            auth_token = self.api_key
        
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    
    def _make_request(self, prompt: str, **kwargs) -> str:
        """发送请求到API"""
        import requests
        
        headers = self._build_headers()
        data = self._build_request_data(prompt, **kwargs)
        
        api_endpoint = self.api_url
        if not api_endpoint.endswith("/chat/completions"):
            api_endpoint = f"{self.api_url.rstrip('/')}/chat/completions"
        
        response = requests.post(
            api_endpoint,
            headers=headers,
            json=data,
            timeout=kwargs.get("timeout", 60)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            error_msg = f"API请求失败: {response.status_code}"
            logger.error(f"{error_msg}, 响应: {response.text}")
            raise LLMException(error_msg, details={"status_code": response.status_code, "response": response.text})
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not self.enabled:
            raise LLMException("讯飞星火大模型不可用，请检查配置")
        
        try:
            return self._make_request(prompt, **kwargs)
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"讯飞星火大模型调用失败: {str(e)}")
            raise LLMException(f"模型调用失败: {str(e)}")
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """流式生成文本"""
        if not self.enabled:
            raise LLMException("讯飞星火大模型不可用，请检查配置")
        
        import requests
        
        headers = self._build_headers()
        data = self._build_request_data(prompt, stream=True, **kwargs)
        
        api_endpoint = self.api_url
        if not api_endpoint.endswith("/chat/completions"):
            api_endpoint = f"{self.api_url.rstrip('/')}/chat/completions"
        
        try:
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=data,
                timeout=kwargs.get("timeout", 120),
                stream=True
            )
            
            if response.status_code != 200:
                raise LLMException(f"API请求失败: {response.status_code}")
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"流式生成失败: {str(e)}")
            raise LLMException(f"流式生成失败: {str(e)}")
    
    async def generate_async(self, prompt: str, **kwargs) -> str:
        """异步生成文本"""
        import httpx
        
        if not self.enabled:
            raise LLMException("讯飞星火大模型不可用，请检查配置")
        
        headers = self._build_headers()
        data = self._build_request_data(prompt, **kwargs)
        
        api_endpoint = self.api_url
        if not api_endpoint.endswith("/chat/completions"):
            api_endpoint = f"{self.api_url.rstrip('/')}/chat/completions"
        
        try:
            async with httpx.AsyncClient(timeout=kwargs.get("timeout", 60)) as client:
                response = await client.post(
                    api_endpoint,
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise LLMException(f"API请求失败: {response.status_code}")
                    
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"异步生成失败: {str(e)}")
            raise LLMException(f"异步生成失败: {str(e)}")
    
    async def generate_stream_async(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成文本"""
        if not self.enabled:
            raise LLMException("讯飞星火大模型不可用，请检查配置")
        
        headers = self._build_headers()
        data = self._build_request_data(prompt, stream=True, **kwargs)
        
        api_endpoint = self.api_url
        if not api_endpoint.endswith("/chat/completions"):
            api_endpoint = f"{self.api_url.rstrip('/')}/chat/completions"
        
        try:
            async with httpx.AsyncClient(timeout=kwargs.get("timeout", 120)) as client:
                async with client.stream(
                    "POST",
                    api_endpoint,
                    headers=headers,
                    json=data
                ) as response:
                    if response.status_code != 200:
                        raise LLMException(f"API请求失败: {response.status_code}")
                    
                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        delta = chunk['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                                    
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"异步流式生成失败: {str(e)}")
            raise LLMException(f"异步流式生成失败: {str(e)}")


class RuleMatchingEngine:
    """规则匹配引擎"""
    
    def __init__(self):
        """初始化规则匹配引擎"""
        self.rules = []
        self.load_rules()
    
    def load_rules(self):
        """加载规则"""
        try:
            self.rules = []
            logger.info("规则匹配引擎初始化完成")
        except Exception as e:
            logger.error(f"规则加载失败: {str(e)}")
            self.rules = []
    
    def match(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """匹配规则"""
        try:
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
        self.providers: Dict[str, LLMProvider] = {}
        self.rule_engine = RuleMatchingEngine()
        self._init_providers()
    
    def _init_providers(self):
        """初始化LLM提供商"""
        xunfei_llm = XunfeiSparkLLM()
        if xunfei_llm.is_available():
            self.providers["xunfei"] = xunfei_llm
            logger.info("讯飞星火大模型已启用")
        else:
            logger.warning("讯飞星火大模型配置不完整，请检查配置文件")
    
    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """获取LLM提供商"""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """列出所有可用的提供商"""
        return list(self.providers.keys())
    
    def get_default_provider(self) -> Optional[LLMProvider]:
        """获取默认提供商"""
        if self.providers:
            return next(iter(self.providers.values()))
        return None
    
    def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """生成文本"""
        if provider and provider in self.providers:
            return self.providers[provider].generate(prompt, **kwargs)
        
        default_provider = self.get_default_provider()
        if default_provider:
            return default_provider.generate(prompt, **kwargs)
        
        rule_result = self.rule_engine.match(prompt)
        return rule_result.get("result", "没有可用的LLM提供商")
    
    def generate_stream(self, prompt: str, provider: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        """流式生成文本"""
        if provider and provider in self.providers:
            yield from self.providers[provider].generate_stream(prompt, **kwargs)
            return
        
        default_provider = self.get_default_provider()
        if default_provider:
            yield from default_provider.generate_stream(prompt, **kwargs)
            return
        
        yield "没有可用的LLM提供商"
    
    async def generate_async(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """异步生成文本"""
        if provider and provider in self.providers:
            return await self.providers[provider].generate_async(prompt, **kwargs)
        
        default_provider = self.get_default_provider()
        if default_provider:
            return await default_provider.generate_async(prompt, **kwargs)
        
        return "没有可用的LLM提供商"
    
    async def generate_stream_async(self, prompt: str, provider: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成文本"""
        if provider and provider in self.providers:
            async for chunk in self.providers[provider].generate_stream_async(prompt, **kwargs):
                yield chunk
            return
        
        default_provider = self.get_default_provider()
        if default_provider:
            async for chunk in default_provider.generate_stream_async(prompt, **kwargs):
                yield chunk
            return
        
        yield "没有可用的LLM提供商"
    
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


_llm_manager_instance = None

def _get_llm_manager():
    """获取LLM管理器单例（内部使用）"""
    global _llm_manager_instance
    if _llm_manager_instance is None:
        _llm_manager_instance = LLMManager()
    return _llm_manager_instance

def __getattr__(name):
    """延迟初始化llm_manager"""
    if name == "llm_manager":
        return _get_llm_manager()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class _LLMManagerProxy:
    """LLM管理器代理类，支持延迟初始化"""
    def __getattr__(self, name):
        return getattr(_get_llm_manager(), name)

llm_manager = _LLMManagerProxy()
