"""
统一的Prompt管理模块
整合了app/prompt_manager.py和app/rag/prompt_manager.py的功能
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config_manager import settings


class PromptManager:
    """统一的Prompt管理类，支持多种提示词模板管理"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化Prompt管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_path = Path("./config/prompts.json")
        self.config_dir = self.config_path.parent
        self.config_dir.mkdir(exist_ok=True)
        
        # 默认系统提示词
        self.default_system_prompt = """你是一个专业的证书审核助手，专门帮助用户分析各类证书的加分情况。
请根据用户提供的证书信息，按照最新的审核标准进行评分。
请提供详细的评分理由，包括具体的加分项和可能的扣分项。"""
        
        # 默认用户提示词
        self.default_user_prompt = """请帮我分析以下证书的加分情况：

证书名称：{cert_name}
证书等级：{cert_level}
发证机构：{cert_issuer}
获得时间：{cert_date}
证书编号：{cert_number}

请按照以下格式提供分析结果：
1. 证书有效性评估
2. 具体加分分数
3. 加分理由
4. 注意事项"""
        
        # 默认聊天系统提示词
        self.default_chat_system_prompt = """你是一个专业的证书审核助手，可以回答用户关于证书审核、加分标准等问题。
请以专业、准确、友好的方式回答用户的问题。"""
        
        # 规则匹配提示词
        self.rule_matching_prompt = """你是一个专业的规则匹配助手，请根据用户的问题，从给定的规则中找到最相关的内容。

用户问题：{query}

相关规则：
{context}

请根据以上规则，回答用户的问题。如果规则中没有直接相关的内容，请说明并提供一般性建议。"""
        
        # 聊天提示词
        self.chat_prompt = """你是一个专业的证书审核助手，可以回答用户关于证书审核、加分标准等问题。

用户问题：{query}

相关参考信息：
{context}

请根据以上信息，以专业、准确、友好的方式回答用户的问题。"""
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.system_prompt = config.get('system_prompt', self.default_system_prompt)
                    self.user_prompt = config.get('user_prompt', self.default_user_prompt)
                    self.chat_system_prompt = config.get('chat_system_prompt', self.default_chat_system_prompt)
                    self.custom_prompts = config.get('custom_prompts', {})
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self._reset_to_default()
        else:
            self._reset_to_default()
    
    def _reset_to_default(self):
        """重置为默认配置"""
        self.system_prompt = self.default_system_prompt
        self.user_prompt = self.default_user_prompt
        self.chat_system_prompt = self.default_chat_system_prompt
        self.custom_prompts = {}
        self.save_config()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'system_prompt': self.system_prompt,
                'user_prompt': self.user_prompt,
                'chat_system_prompt': self.chat_system_prompt,
                'custom_prompts': self.custom_prompts
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'system_prompt': self.system_prompt,
            'user_prompt': self.user_prompt,
            'chat_system_prompt': self.chat_system_prompt,
            'custom_prompts': self.custom_prompts
        }
    
    def update_prompt(self, system_prompt: str = None, user_prompt: str = None, 
                     chat_system_prompt: str = None) -> Dict[str, Any]:
        """更新提示词"""
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if user_prompt is not None:
            self.user_prompt = user_prompt
        if chat_system_prompt is not None:
            self.chat_system_prompt = chat_system_prompt
        
        self.save_config()
        return self.get_current_config()
    
    def reset_to_default(self) -> Dict[str, Any]:
        """重置为默认配置"""
        self._reset_to_default()
        return self.get_current_config()
    
    def get_rule_matching_prompt(self, query: str, context: str) -> str:
        """获取规则匹配提示词"""
        return self.rule_matching_prompt.format(query=query, context=context)
    
    def get_chat_prompt(self, query: str, context: str) -> str:
        """获取聊天提示词"""
        return self.chat_prompt.format(query=query, context=context)
    
    def get_cert_analysis_prompt(self, cert_name: str, cert_level: str, 
                                cert_issuer: str, cert_date: str, cert_number: str) -> str:
        """获取证书分析提示词"""
        return self.user_prompt.format(
            cert_name=cert_name,
            cert_level=cert_level,
            cert_issuer=cert_issuer,
            cert_date=cert_date,
            cert_number=cert_number
        )
    
    def add_custom_prompt(self, name: str, template: str) -> bool:
        """添加自定义提示词模板"""
        try:
            self.custom_prompts[name] = template
            self.save_config()
            return True
        except Exception as e:
            print(f"添加自定义提示词失败: {e}")
            return False
    
    def get_custom_prompt(self, name: str) -> Optional[str]:
        """获取自定义提示词模板"""
        return self.custom_prompts.get(name)
    
    def remove_custom_prompt(self, name: str) -> bool:
        """删除自定义提示词模板"""
        try:
            if name in self.custom_prompts:
                del self.custom_prompts[name]
                self.save_config()
                return True
            return False
        except Exception as e:
            print(f"删除自定义提示词失败: {e}")
            return False
    
    def list_custom_prompts(self) -> Dict[str, str]:
        """列出所有自定义提示词模板"""
        return self.custom_prompts.copy()


# 创建全局实例（延迟初始化）
prompt_manager = None

def _get_prompt_manager():
    """获取Prompt管理器单例（内部使用）"""
    global prompt_manager
    if prompt_manager is None:
        prompt_manager = PromptManager()
    return prompt_manager

def __getattr__(name):
    """延迟初始化prompt_manager"""
    if name == "prompt_manager":
        return _get_prompt_manager()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")